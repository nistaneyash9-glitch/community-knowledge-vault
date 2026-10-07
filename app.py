import os
import mysql.connector
import functools
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import timedelta

from config import Config
from db import db

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'ckv_session'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper: Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Decorator: Login Required
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator: Admin Required
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin authentication required for this action.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Serve Uploaded Files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==========================================================================
# 1. HOMEPAGE ROUTE
# ==========================================================================
@app.route('/')
def index():
    # Fetch top 4 featured approved knowledge items with author and stats
    sql_featured = '''
        SELECT k.*, c.name AS category_name, u.name AS author_name, u.profile_image AS author_image,
               COALESCE((SELECT COUNT(*) FROM helpful_votes hv WHERE hv.knowledge_id = k.id), 0) AS helpful_count,
               COALESCE((SELECT AVG(rating) FROM ratings r WHERE r.knowledge_id = k.id), 0.0) AS avg_rating
        FROM knowledge k
        JOIN categories c ON k.category_id = c.id
        JOIN users u ON k.user_id = u.id
        WHERE k.status = 'approved'
        ORDER BY k.created_at DESC
        LIMIT 4;
    '''
    featured_knowledge = db.fetchall(sql_featured)

    # Fetch categories with knowledge count
    sql_cats = '''
        SELECT c.*, COUNT(k.id) AS knowledge_count
        FROM categories c
        LEFT JOIN knowledge k ON c.id = k.category_id AND k.status = 'approved'
        GROUP BY c.id
        ORDER BY c.name ASC;
    '''
    categories = db.fetchall(sql_cats)

    return render_template('index.html', featured_knowledge=featured_knowledge, categories=categories)

# ==========================================================================
# 2. EXPLORE ROUTE (SEARCH & MULTI-FILTER REPOSITORY)
# ==========================================================================
@app.route('/explore')
def explore():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    skill_level = request.args.get('skill_level', '').strip()
    sort = request.args.get('sort', 'newest').strip()

    # Build parameterized query safely
    query_parts = ["k.status = 'approved'"]
    params = []

    if q:
        query_parts.append("(k.title LIKE %s OR k.description LIKE %s OR k.tags LIKE %s OR k.location LIKE %s)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term, search_term])

    if category:
        query_parts.append("c.name = %s")
        params.append(category)

    if skill_level:
        query_parts.append("k.skill_level = %s")
        params.append(skill_level)

    where_clause = " AND ".join(query_parts)

    order_by = "k.created_at DESC"
    if sort == 'title':
        order_by = "k.title ASC"
    elif sort == 'helpful':
        order_by = "helpful_count DESC"

    sql_explore = f'''
        SELECT k.*, c.name AS category_name, u.name AS author_name, u.profile_image AS author_image,
               COALESCE((SELECT COUNT(*) FROM helpful_votes hv WHERE hv.knowledge_id = k.id), 0) AS helpful_count,
               COALESCE((SELECT AVG(rating) FROM ratings r WHERE r.knowledge_id = k.id), 0.0) AS avg_rating
        FROM knowledge k
        JOIN categories c ON k.category_id = c.id
        JOIN users u ON k.user_id = u.id
        WHERE {where_clause}
        ORDER BY {order_by};
    '''
    knowledge_items = db.fetchall(sql_explore, tuple(params))
    categories = db.fetchall("SELECT * FROM categories ORDER BY name ASC;")

    return render_template('explore.html',
                           knowledge_items=knowledge_items,
                           categories=categories,
                           selected_category=category,
                           selected_skill=skill_level,
                           selected_sort=sort,
                           query_q=q)

# ==========================================================================
# 3. KNOWLEDGE DETAILS ROUTE
# ==========================================================================
@app.route('/knowledge/<int:knowledge_id>')
def knowledge_detail(knowledge_id):
    sql_item = '''
        SELECT k.*, c.name AS category_name, u.name AS author_name, u.location AS author_location,
               u.profile_image AS author_image, u.id AS author_id,
               COALESCE((SELECT COUNT(*) FROM helpful_votes hv WHERE hv.knowledge_id = k.id), 0) AS helpful_count,
               COALESCE((SELECT AVG(rating) FROM ratings r WHERE r.knowledge_id = k.id), 0.0) AS avg_rating
        FROM knowledge k
        JOIN categories c ON k.category_id = c.id
        JOIN users u ON k.user_id = u.id
        WHERE k.id = %s;
    '''
    item = db.fetchone(sql_item, (knowledge_id,))
    if not item:
        flash('Knowledge record not found.', 'danger')
        return redirect(url_for('explore'))

    # Access control: prevent non-author and non-admin from viewing pending/rejected items
    if item['status'] != 'approved':
        current_user_id = session.get('user_id')
        user_role = session.get('role')
        if current_user_id != item['user_id'] and user_role != 'admin':
            flash('This knowledge submission is currently pending moderation review.', 'warning')
            return redirect(url_for('explore'))

    # Check if current user voted helpful
    has_voted_helpful = False
    if session.get('user_id'):
        vote_check = db.fetchone("SELECT id FROM helpful_votes WHERE knowledge_id = %s AND user_id = %s;", (knowledge_id, session['user_id']))
        has_voted_helpful = bool(vote_check)

    # Ratings
    ratings = db.fetchall("SELECT r.*, u.name AS learner_name FROM ratings r JOIN users u ON r.learner_id = u.id WHERE r.knowledge_id = %s ORDER BY r.created_at DESC;", (knowledge_id,))

    # Questions & Answers
    sql_questions = '''
        SELECT q.*, u.name AS asker_name
        FROM questions q
        JOIN users u ON q.user_id = u.id
        WHERE q.knowledge_id = %s
        ORDER BY q.created_at DESC;
    '''
    questions = db.fetchall(sql_questions, (knowledge_id,))
    for q in questions:
        sql_answers = '''
            SELECT a.*, u.name AS answerer_name
            FROM answers a
            JOIN users u ON a.user_id = u.id
            WHERE a.question_id = %s
            ORDER BY a.created_at ASC;
        '''
        q['answers'] = db.fetchall(sql_answers, (q['id'],))

    return render_template('knowledge.html',
                           item=item,
                           ratings=ratings,
                           questions=questions,
                           has_voted_helpful=has_voted_helpful)

# ==========================================================================
# 4. SHARE KNOWLEDGE ROUTE
# ==========================================================================
@app.route('/share', methods=['GET', 'POST'])
@login_required
def share():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id')
        skill_level = request.form.get('skill_level', 'Beginner')
        location = request.form.get('location', session.get('location', 'Amravati')).strip()
        language = request.form.get('language', 'English').strip()
        tags = request.form.get('tags', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not category_id or not description:
            flash('Please complete all required fields (Title, Category, Description).', 'danger')
            return redirect(url_for('share'))

        # Handle image file upload
        image_filename = None
        file = request.files.get('image')
        if file and file.filename != '':
            if allowed_file(file.filename):
                sec_filename = secure_filename(file.filename)
                # Ensure unique filename
                image_filename = f"{session['user_id']}_{sec_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            else:
                flash('Invalid image type. Please upload JPG, PNG, or WEBP.', 'danger')
                return redirect(url_for('share'))

        # Insert new knowledge record with status = 'pending'
        sql_insert = '''
            INSERT INTO knowledge (user_id, category_id, title, description, skill_level, language, location, tags, image, status, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', 0);
        '''
        db.execute(sql_insert, (session['user_id'], category_id, title, description, skill_level, language, location, tags, image_filename))

        flash('Knowledge submitted successfully! It is queued for elder & admin verification before public release.', 'success')
        return redirect(url_for('profile'))

    categories = db.fetchall("SELECT * FROM categories ORDER BY name ASC;")
    return render_template('share.html', categories=categories)

# ==========================================================================
# 5. USER REGISTRATION ROUTE
# ==========================================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        location = request.form.get('location', 'Amravati').strip()
        language = request.form.get('language', 'English').strip()

        if not name or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Password confirmation does not match.', 'danger')
            return redirect(url_for('register'))

        # Check duplicate email
        existing = db.fetchone("SELECT id FROM users WHERE email = %s;", (email,))
        if existing:
            flash('Email address is already registered. Please sign in.', 'warning')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        sql_register = '''
            INSERT INTO users (name, email, password, location, language, role)
            VALUES (%s, %s, %s, %s, %s, 'user');
        '''
        db.execute(sql_register, (name, email, hashed_password, location, language))

        # Fetch created user record to guarantee valid session user_id
        created_user = db.fetchone("SELECT * FROM users WHERE email = %s;", (email,))
        if created_user:
            session.permanent = True
            session['user_id'] = created_user['id']
            session['user_name'] = created_user['name']
            session['role'] = created_user['role']
            session['location'] = created_user['location']
            session.modified = True

        flash(f'Account created successfully! Welcome to the Vault, {name}.', 'success')
        return redirect(url_for('profile'))

    return render_template('register.html')

# ==========================================================================
# 6. USER LOGIN & LOGOUT ROUTES
# ==========================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = db.fetchone("SELECT * FROM users WHERE email = %s;", (email,))
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            session['location'] = user['location']
            session.modified = True

            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('profile'))
        else:
            flash('Invalid email address or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out.', 'info')
    return redirect(url_for('index'))

# ==========================================================================
# 7. USER PROFILE ROUTE (5 PERSONAL STATISTICS)
# ==========================================================================
@app.route('/profile')
@app.route('/profile/<int:user_id>')
def profile(user_id=None):
    target_id = user_id or session.get('user_id')
    if not target_id:
        flash('Please sign in to view your profile.', 'warning')
        return redirect(url_for('login'))

    target_user = db.fetchone("SELECT * FROM users WHERE id = %s;", (target_id,))
    if not target_user:
        flash('User profile not found.', 'danger')
        return redirect(url_for('index'))

    # Compute 5 Personal Statistics
    # 1. Knowledge Shared
    ks_res = db.fetchone("SELECT COUNT(*) AS cnt FROM knowledge WHERE user_id = %s;", (target_id,))
    knowledge_shared = ks_res['cnt'] if ks_res else 0

    # 2. Helpful Votes Received
    hv_res = db.fetchone("SELECT COUNT(*) AS cnt FROM helpful_votes hv JOIN knowledge k ON hv.knowledge_id = k.id WHERE k.user_id = %s;", (target_id,))
    helpful_votes = hv_res['cnt'] if hv_res else 0

    # 3. Learning Requests
    lr_res = db.fetchone("SELECT COUNT(*) AS cnt FROM learning_requests WHERE teacher_id = %s OR learner_id = %s;", (target_id, target_id))
    learning_requests = lr_res['cnt'] if lr_res else 0

    # 4. Average Rating
    ar_res = db.fetchone("SELECT AVG(r.rating) AS avg_score FROM ratings r JOIN knowledge k ON r.knowledge_id = k.id WHERE k.user_id = %s;", (target_id,))
    avg_rating = float(ar_res['avg_score']) if ar_res and ar_res['avg_score'] is not None else 0.0

    # 5. Verified Knowledge
    vk_res = db.fetchone("SELECT COUNT(*) AS cnt FROM knowledge WHERE user_id = %s AND is_verified = 1;", (target_id,))
    verified_count = vk_res['cnt'] if vk_res else 0

    stats = {
        'knowledge_shared': knowledge_shared,
        'helpful_votes': helpful_votes,
        'learning_requests': learning_requests,
        'avg_rating': avg_rating,
        'verified_count': verified_count
    }

    # Fetch user's published & pending knowledge
    sql_user_k = '''
        SELECT k.*, c.name AS category_name,
               COALESCE((SELECT COUNT(*) FROM helpful_votes hv WHERE hv.knowledge_id = k.id), 0) AS helpful_count,
               COALESCE((SELECT AVG(rating) FROM ratings r WHERE r.knowledge_id = k.id), 0) AS avg_rating
        FROM knowledge k
        JOIN categories c ON k.category_id = c.id
        WHERE k.user_id = %s
        ORDER BY k.created_at DESC;
    '''
    user_knowledge = db.fetchall(sql_user_k, (target_id,))
    for item in user_knowledge:
        item['avg_rating'] = float(item['avg_rating']) if item.get('avg_rating') is not None else 0.0

    return render_template('profile.html', target_user=target_user, stats=stats, user_knowledge=user_knowledge)

@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    language = request.form.get('language', '').strip()

    if not name or not location:
        flash('Name and location are required.', 'danger')
        return redirect(url_for('profile'))

    image_filename = None
    file = request.files.get('profile_image')
    if file and file.filename != '':
        if allowed_file(file.filename):
            sec_filename = secure_filename(file.filename)
            image_filename = f"avatar_{user_id}_{sec_filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        else:
            flash('Invalid avatar image type.', 'danger')
            return redirect(url_for('profile'))

    if image_filename:
        db.execute("UPDATE users SET name = %s, location = %s, language = %s, profile_image = %s WHERE id = %s;",
                   (name, location, language, image_filename, user_id))
    else:
        db.execute("UPDATE users SET name = %s, location = %s, language = %s WHERE id = %s;",
                   (name, location, language, user_id))

    session['user_name'] = name
    session['location'] = location
    flash('Profile details updated successfully!', 'success')
    return redirect(url_for('profile'))

# ==========================================================================
# 8. LEARNING REQUESTS MANAGEMENT
# ==========================================================================
@app.route('/requests')
@login_required
def requests_page():
    user_id = session['user_id']

    # Incoming requests (User is teacher)
    sql_inc = '''
        SELECT lr.*, k.title AS knowledge_title, u.name AS learner_name
        FROM learning_requests lr
        JOIN knowledge k ON lr.knowledge_id = k.id
        JOIN users u ON lr.learner_id = u.id
        WHERE lr.teacher_id = %s
        ORDER BY lr.created_at DESC;
    '''
    incoming_requests = db.fetchall(sql_inc, (user_id,))

    # Outgoing requests (User is learner)
    sql_out = '''
        SELECT lr.*, k.title AS knowledge_title, u.name AS teacher_name,
               (SELECT COUNT(*) FROM ratings r WHERE r.learning_request_id = lr.id AND r.learner_id = %s) AS has_rated
        FROM learning_requests lr
        JOIN knowledge k ON lr.knowledge_id = k.id
        JOIN users u ON lr.teacher_id = u.id
        WHERE lr.learner_id = %s
        ORDER BY lr.created_at DESC;
    '''
    outgoing_requests = db.fetchall(sql_out, (user_id, user_id))

    return render_template('requests.html', incoming_requests=incoming_requests, outgoing_requests=outgoing_requests)

@app.route('/request_learn/<int:knowledge_id>', methods=['POST'])
@login_required
def request_learn(knowledge_id):
    message = request.form.get('message', '').strip()
    k_item = db.fetchone("SELECT user_id FROM knowledge WHERE id = %s;", (knowledge_id,))
    if not k_item:
        flash('Knowledge record not found.', 'danger')
        return redirect(url_for('explore'))

    teacher_id = k_item['user_id']
    learner_id = session['user_id']

    if teacher_id == learner_id:
        flash('You cannot send a learning request to your own knowledge post.', 'warning')
        return redirect(url_for('knowledge_detail', knowledge_id=knowledge_id))

    db.execute('''
        INSERT INTO learning_requests (knowledge_id, teacher_id, learner_id, message, status)
        VALUES (%s, %s, %s, %s, 'pending');
    ''', (knowledge_id, teacher_id, learner_id, message))

    flash('Learning request sent to the custodian mentor!', 'success')
    return redirect(url_for('requests_page'))

@app.route('/request/<action>/<int:request_id>', methods=['POST'])
@login_required
def handle_request(action, request_id):
    req_item = db.fetchone("SELECT * FROM learning_requests WHERE id = %s;", (request_id,))
    if not req_item or req_item['teacher_id'] != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('requests_page'))

    current_status = req_item['status']
    if action == 'accept' and current_status == 'pending':
        db.execute("UPDATE learning_requests SET status = 'accepted' WHERE id = %s;", (request_id,))
        flash('Learning request accepted!', 'success')
    elif action == 'reject' and current_status == 'pending':
        db.execute("UPDATE learning_requests SET status = 'rejected' WHERE id = %s;", (request_id,))
        flash('Learning request rejected.', 'info')
    elif action == 'complete' and current_status == 'accepted':
        db.execute("UPDATE learning_requests SET status = 'completed' WHERE id = %s;", (request_id,))
        flash('Learning interaction marked as completed!', 'success')
    else:
        flash('Invalid status transition for this learning request.', 'warning')

    return redirect(url_for('requests_page'))

# ==========================================================================
# 9. RATINGS, HELPFUL VOTES & Q&A
# ==========================================================================
@app.route('/rate/<int:knowledge_id>', methods=['POST'])
@login_required
def submit_rating(knowledge_id):
    try:
        rating = int(request.form.get('rating', 5))
    except ValueError:
        flash('Invalid rating value.', 'danger')
        return redirect(url_for('requests_page'))

    if rating < 1 or rating > 5:
        flash('Rating must be an integer between 1 and 5.', 'warning')
        return redirect(url_for('requests_page'))

    learning_request_id = request.form.get('learning_request_id')

    # Verify that a completed learning request exists for this learner & knowledge
    req_check = db.fetchone("SELECT id FROM learning_requests WHERE id = %s AND learner_id = %s AND knowledge_id = %s AND status = 'completed';",
                           (learning_request_id, session['user_id'], knowledge_id))
    if not req_check:
        flash('You can only rate after completing a learning request for this knowledge.', 'warning')
        return redirect(url_for('requests_page'))

    # Prevent duplicate rating
    existing = db.fetchone("SELECT id FROM ratings WHERE knowledge_id = %s AND learner_id = %s;", (knowledge_id, session['user_id']))
    if existing:
        flash('You have already submitted a rating for this knowledge.', 'warning')
        return redirect(url_for('requests_page'))

    db.execute('''
        INSERT INTO ratings (knowledge_id, learner_id, learning_request_id, rating, review)
        VALUES (%s, %s, %s, %s, %s);
    ''', (knowledge_id, session['user_id'], learning_request_id, rating, request.form.get('review', '').strip()))

    flash('Thank you for rating your learning experience!', 'success')
    return redirect(url_for('requests_page'))

@app.route('/helpful/<int:knowledge_id>', methods=['POST'])
@login_required
def helpful_vote(knowledge_id):
    existing = db.fetchone("SELECT id FROM helpful_votes WHERE knowledge_id = %s AND user_id = %s;", (knowledge_id, session['user_id']))
    if existing:
        db.execute("DELETE FROM helpful_votes WHERE id = %s;", (existing['id'],))
        flash('Helpful vote removed.', 'info')
    else:
        db.execute("INSERT INTO helpful_votes (knowledge_id, user_id) VALUES (%s, %s);", (knowledge_id, session['user_id']))
        flash('Marked as helpful! Thank you for supporting community knowledge.', 'success')

    return redirect(url_for('knowledge_detail', knowledge_id=knowledge_id))

@app.route('/ask_question/<int:knowledge_id>', methods=['POST'])
@login_required
def ask_question(knowledge_id):
    question_text = request.form.get('question_text', '').strip()
    if question_text:
        db.execute("INSERT INTO questions (knowledge_id, user_id, question_text) VALUES (%s, %s, %s);",
                   (knowledge_id, session['user_id'], question_text))
        flash('Question posted to community discussion!', 'success')
    return redirect(url_for('knowledge_detail', knowledge_id=knowledge_id))

@app.route('/answer_question/<int:question_id>', methods=['POST'])
@login_required
def answer_question(question_id):
    answer_text = request.form.get('answer_text', '').strip()
    q = db.fetchone("SELECT knowledge_id FROM questions WHERE id = %s;", (question_id,))
    if answer_text and q:
        db.execute("INSERT INTO answers (question_id, user_id, answer_text) VALUES (%s, %s, %s);",
                   (question_id, session['user_id'], answer_text))
        flash('Answer posted!', 'success')
        return redirect(url_for('knowledge_detail', knowledge_id=q['knowledge_id']))
    return redirect(url_for('explore'))

@app.route('/report/<int:knowledge_id>', methods=['POST'])
@login_required
def report_knowledge(knowledge_id):
    reason = request.form.get('reason', 'Other').strip()
    description = request.form.get('description', '').strip()
    db.execute("INSERT INTO reports (knowledge_id, reported_by, reason, description, status) VALUES (%s, %s, %s, %s, 'pending');",
               (knowledge_id, session['user_id'], reason, description))
    flash('Report submitted to community moderators for review.', 'info')
    return redirect(url_for('knowledge_detail', knowledge_id=knowledge_id))

# ==========================================================================
# 10. ABOUT ROUTE
# ==========================================================================
@app.route('/about')
def about():
    return render_template('about.html')

# ==========================================================================
# 11. ADMIN MODERATION DASHBOARD & ACTIONS
# ==========================================================================
@app.route('/admin')
@admin_required
def admin():
    # Overall statistics
    total_users = db.fetchone("SELECT COUNT(*) AS cnt FROM users;")['cnt']
    total_knowledge = db.fetchone("SELECT COUNT(*) AS cnt FROM knowledge;")['cnt']
    pending_k = db.fetchone("SELECT COUNT(*) AS cnt FROM knowledge WHERE status = 'pending';")['cnt']
    approved_k = db.fetchone("SELECT COUNT(*) AS cnt FROM knowledge WHERE status = 'approved';")['cnt']
    verified_k = db.fetchone("SELECT COUNT(*) AS cnt FROM knowledge WHERE is_verified = 1;")['cnt']
    pending_reports = db.fetchone("SELECT COUNT(*) AS cnt FROM reports WHERE status = 'pending';")['cnt']

    stats = {
        'total_users': total_users,
        'total_knowledge': total_knowledge,
        'pending_knowledge': pending_k,
        'approved_knowledge': approved_k,
        'verified_knowledge': verified_k,
        'pending_reports': pending_reports
    }

    # Lists
    pending_queue = db.fetchall('''
        SELECT k.*, c.name AS category_name, u.name AS author_name
        FROM knowledge k
        JOIN categories c ON k.category_id = c.id
        JOIN users u ON k.user_id = u.id
        WHERE k.status = 'pending'
        ORDER BY k.created_at DESC;
    ''')

    approved_list = db.fetchall('''
        SELECT k.*, c.name AS category_name, u.name AS author_name
        FROM knowledge k
        JOIN categories c ON k.category_id = c.id
        JOIN users u ON k.user_id = u.id
        WHERE k.status = 'approved'
        ORDER BY k.created_at DESC;
    ''')

    reports_list = db.fetchall('''
        SELECT r.*, k.title AS knowledge_title, u.name AS reporter_name
        FROM reports r
        JOIN knowledge k ON r.knowledge_id = k.id
        JOIN users u ON r.reported_by = u.id
        ORDER BY r.created_at DESC;
    ''')

    users_list = db.fetchall("SELECT * FROM users ORDER BY created_at DESC;")

    return render_template('admin.html',
                           stats=stats,
                           pending_queue=pending_queue,
                           approved_list=approved_list,
                           reports_list=reports_list,
                           users_list=users_list)

@app.route('/admin/approve/<int:knowledge_id>', methods=['POST'])
@admin_required
def admin_approve_knowledge(knowledge_id):
    db.execute("UPDATE knowledge SET status = 'approved' WHERE id = %s;", (knowledge_id,))
    flash('Knowledge record approved & published to community repository!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:knowledge_id>', methods=['POST'])
@admin_required
def admin_reject_knowledge(knowledge_id):
    db.execute("UPDATE knowledge SET status = 'rejected' WHERE id = %s;", (knowledge_id,))
    flash('Knowledge record rejected.', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/verify/<int:knowledge_id>', methods=['POST'])
@admin_required
def admin_verify_knowledge(knowledge_id):
    db.execute("UPDATE knowledge SET is_verified = 1 WHERE id = %s;", (knowledge_id,))
    flash('Knowledge record verified with ✓ Verified badge!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:knowledge_id>', methods=['POST'])
@admin_required
def admin_delete_knowledge(knowledge_id):
    db.execute("DELETE FROM knowledge WHERE id = %s;", (knowledge_id,))
    flash('Knowledge record permanently deleted.', 'warning')
    return redirect(url_for('admin'))

@app.route('/admin/report/resolve/<int:report_id>', methods=['POST'])
@admin_required
def admin_resolve_report(report_id):
    db.execute("UPDATE reports SET status = 'resolved' WHERE id = %s;", (report_id,))
    flash('Report marked as resolved.', 'success')
    return redirect(url_for('admin'))

# ==========================================================================
# CATCH-ALL ROUTE FOR .html URLs (REDIRECTS TO CANONICAL FLASK ROUTES)
# ==========================================================================
@app.route('/<page_name>.html')
def legacy_html_redirect(page_name):
    clean_routes = {
        'index': '/',
        'home': '/',
        'explore': '/explore',
        'share': '/share',
        'login': '/login',
        'register': '/register',
        'profile': '/profile',
        'requests': '/requests',
        'about': '/about',
        'admin': '/admin'
    }
    target = clean_routes.get(page_name.lower(), '/')
    return redirect(target)

# ==========================================================================
# MYSQL CONNECTION ERROR HANDLER
# ==========================================================================
@app.errorhandler(mysql.connector.Error)
def handle_mysql_error(err):
    if err.errno == 1045:
        msg = f"""
        <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 4rem auto; padding: 2rem; background: #12141a; color: #ffffff; border: 1px solid #ff4d4d; border-radius: 8px;">
          <h2 style="color: #ff4d4d; margin-top: 0;">MySQL Database Connection Notice</h2>
          <p>Access denied for user <code>'{Config.MYSQL_USER}'@'{Config.MYSQL_HOST}'</code> (Error 1045).</p>
          <p style="color: #a0a5b5;">Your local MySQL server rejected the password currently configured in <code>config.py</code>.</p>
          <hr style="border: 0; border-top: 1px solid #2a2e3d; margin: 1.5rem 0;">
          <h4 style="margin-bottom: 0.5rem; color: #d8f844;">How to resolve:</h4>
          <ol style="line-height: 1.8; color: #d0d5e5;">
            <li>Open <strong style="color: #ffffff;">config.py</strong> in your project root folder.</li>
            <li>Update <code style="color: #d8f844;">MYSQL_PASSWORD</code> on line 9 to your actual local MySQL password (or <code style="color: #d8f844;">''</code> if using XAMPP/WAMP without a password).</li>
            <li>Save the file and refresh your browser.</li>
          </ol>
        </div>
        """
        return msg, 500
    return f"<h3>Database Error: {err}</h3>", 500

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    print("==================================================", flush=True)
    print("COMMUNITY KNOWLEDGE VAULT (CKV) SERVER", flush=True)
    print(f"Running on: http://{host}:{port}", flush=True)
    print("==================================================", flush=True)
    try:
        from waitress import serve
        serve(app, host=host, port=port)
    except ImportError:
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        app.run(host=host, port=port)



