import mysql.connector
from mysql.connector import Error as MySQLError
import os
import re
from config import Config

class Database:
    def __init__(self, app=None):
        self.app = app
        self._check_and_init_db()

    def _get_mysql_connection(self, with_db=True):
        kwargs = {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'port': Config.MYSQL_PORT,
            'autocommit': True
        }
        if with_db:
            kwargs['database'] = Config.MYSQL_DB
        return mysql.connector.connect(**kwargs)

    def _check_and_init_db(self):
        try:
            conn = self._get_mysql_connection(with_db=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` DEFAULT CHARACTER SET utf8mb4;")
            cursor.close()
            conn.close()

            # Test connecting with DB
            conn = self._get_mysql_connection(with_db=True)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SHOW TABLES LIKE 'users';")
            result = cursor.fetchone()
            cursor.close()

            if not result:
                self._run_sql_script_mysql(conn)
            self._ensure_seed_users(conn)
            conn.close()
            print("Successfully initialized and connected to MySQL database:", Config.MYSQL_DB)
        except Exception as e:
            err_msg = (
                f"\n========================================================================\n"
                f"DATABASE CONNECTION ERROR:\n"
                f"Failed to connect to MySQL server at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}.\n"
                f"Error Details: {e}\n"
                f"Please verify MySQL server is running and check settings in config.py.\n"
                f"========================================================================\n"
            )
            print(err_msg)

    def _run_sql_script_mysql(self, conn):
        schema_path = os.path.join(Config.BASE_DIR, 'database', 'schema.sql')
        if not os.path.exists(schema_path):
            return
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        sql_content = re.sub(r'CREATE DATABASE.*?;', '', sql_content, flags=re.IGNORECASE)
        sql_content = re.sub(r'USE.*?;', '', sql_content, flags=re.IGNORECASE)

        cursor = conn.cursor()
        for statement in sql_content.split(';'):
            stmt = statement.strip()
            if stmt:
                clean_stmt = re.sub(r'--.*?\n', '', stmt).strip()
                if clean_stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as ex:
                        print(f"Error executing schema statement: {ex}")
        conn.commit()
        cursor.close()

    def _ensure_seed_users(self, conn):
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS cnt FROM users;")
            row = cursor.fetchone()
            cursor.close()
            if not row or row['cnt'] == 0:
                from werkzeug.security import generate_password_hash
                p1 = generate_password_hash('admin123')
                p2 = generate_password_hash('masterweaver2026')
                p3 = generate_password_hash('studentpass123')
                p4 = generate_password_hash('kalyanipass123')
                p5 = generate_password_hash('devrajpass123')
                sql = '''INSERT INTO users (id, name, email, password, location, language, profile_image, role) VALUES
                (1, 'Admin Custodian', 'admin@amravati.in', %s, 'Amravati Central', 'English', 'https://ui-avatars.com/api/?name=Admin+Custodian&background=141c16&color=d8f844&bold=true', 'admin'),
                (2, 'Ramesh Patel', 'ramesh.patel@amravati.in', %s, 'Amravati Old Artisan Quarter', 'English', 'https://ui-avatars.com/api/?name=Ramesh+Patel&background=141c16&color=d8f844&bold=true', 'user'),
                (3, 'Ananya Sharma', 'ananya.sharma@amravati.edu', %s, 'Amravati University Campus', 'English', 'https://ui-avatars.com/api/?name=Ananya+Sharma&background=141c16&color=d8f844&bold=true', 'user'),
                (4, 'Kalyani Devi', 'kalyani.devi@amravati.in', %s, 'Amravati North Valley', 'English', 'https://ui-avatars.com/api/?name=Kalyani+Devi&background=141c16&color=d8f844&bold=true', 'user'),
                (5, 'Prof. Devraj', 'devraj@amravati.in', %s, 'Amravati Heritage Ward', 'English', 'https://ui-avatars.com/api/?name=Prof+Devraj&background=141c16&color=d8f844&bold=true', 'user');'''
                cursor = conn.cursor()
                cursor.execute(sql, (p1, p2, p3, p4, p5))
                conn.commit()
                cursor.close()
        except Exception as ex:
            print(f"Error ensuring seed users: {ex}")

    def get_connection(self):
        return self._get_mysql_connection(with_db=True)

    def fetchall(self, query, params=None):
        params = params or ()
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def fetchone(self, query, params=None):
        params = params or ()
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def execute(self, query, params=None):
        params = params or ()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return last_id

db = Database()
