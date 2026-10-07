# Community Knowledge Vault (CKV)

Community Knowledge Vault (CKV) is a college Community Engagement Project developed to collect and share useful knowledge from the local community. Users can share knowledge, explore existing posts, ask questions and send learning requests. The website is developed using Python Flask, HTML, CSS, JavaScript and MySQL.

**College Project Details:**
- **Institution:** P. R. Pote Patil College of Engineering & Management, Amravati
- **Project Type:** Community Engagement Project (CEP)
- **Project Guide:** Dr. R. R. Bhure
- **Location Focus:** Amravati, Maharashtra

---

## 1. Project Purpose
The purpose of CKV is to provide a digital platform for community members in Amravati to document, organize, and access practical local knowledge across topics such as farming, gardening, cooking, local history, and traditional skills.

---

## 2. Problem Statement
Useful local practices and historical knowledge are often communicated verbally or through personal experience. Without a central place to store this information, valuable guidance can be lost over time. CKV addresses this by offering a simple, accessible website where community members can share step-by-step guides and learn from one another.

---

## 3. Main Features
- **User Authentication:** Registration, login, logout, and profile management with password hashing.
- **Knowledge Sharing:** Form to submit title, category, skill level, description, tags, and photos.
- **Explore & Filter:** Browse knowledge posts by category (Farming, Gardening, Local History, Cooking, Traditional Skills) and search by keyword or skill level.
- **Moderation & Verification:** Admin panel to review pending posts, approve/reject submissions, and mark verified knowledge.
- **Community Q&A:** Ask questions on published posts and receive answers from authors or admins.
- **1-on-1 Learning Requests:** Send requests to connect with knowledge authors for hands-on learning.
- **Helpful Votes & Ratings:** Mark posts as helpful and rate completed learning interactions (1 to 5 stars).
- **Report Content:** Flag incorrect or inappropriate content for admin review.

---

## 4. Technologies Used
- **Frontend:** HTML5, CSS3, JavaScript
- **Backend:** Python Flask
- **Database:** MySQL
- **Connector:** mysql.connector-python
- **WSGI Server:** Waitress (for Windows production deployment)

---

## 5. Database Structure
The project uses a MySQL database (`community_knowledge_vault`) containing 10 normalized tables:
- `users`: Account credentials, locations, roles (`user`, `admin`).
- `categories`: Core topics (Farming, Gardening, Local History, Cooking, Traditional Skills).
- `knowledge`: Main knowledge posts linked to users and categories.
- `skills`: Specific skill catalog mapped to categories.
- `learning_requests`: Workflow table tracking learner-teacher requests.
- `ratings`: Ratings (1-5 stars) and reviews for completed learning requests.
- `helpful_votes`: Helpful click tracking per user and post.
- `questions`: User questions posted on knowledge entries.
- `answers`: Contributor responses to user questions.
- `reports`: Moderation tickets for admin review.

---

## 6. How to Run the Project

### Prerequisites
- Python 3.8+
- MySQL Server (or XAMPP / MariaDB)

### Setup Steps
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup:**
   Import `database/schema.sql` into MySQL:
   ```bash
   mysql -u root -p community_knowledge_vault < database/schema.sql
   ```

3. **Database Configuration:**
   Configure MySQL credentials in `config.py`:
   ```python
   MYSQL_HOST = 'localhost'
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = '' # Set your local MySQL password
   MYSQL_DB = 'community_knowledge_vault'
   MYSQL_PORT = 3306
   ```

4. **Start Application:**
   ```bash
   python app.py
   ```
   Open browser at `http://127.0.0.1:5000`

---

## 7. Team Contribution
- **Project Mentor / Guide:** Dr. R. R. Bhure
- **Student Team:** CEP Project Team Members
- **Contributions:** Field survey, requirement gathering, database schema design, Flask backend implementation, frontend templates, and moderation workflow testing.

---

## 8. Future Scope
- Mobile-responsive UI enhancements.
- Multilingual support (Marathi and Hindi translation).
- Export knowledge guides as downloadable PDF documents for offline community distribution.
