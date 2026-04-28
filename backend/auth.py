from flask import request, jsonify, session
from functools import wraps
from db import get_db
from security import hash_password, verify_password
import re
import mysql.connector


def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def signup_user(email, password, full_name):
    if not validate_email(email):
        return {"error": "Invalid email format"}, 400
    if len(password) < 6:
        return {"error": "Password must be at least 6 characters"}, 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"error": "Email already registered"}, 409

        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)",
            (email, password_hash, full_name)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"success": True, "user_id": user_id, "message": "Account created"}, 201
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()


def login_user(email, password):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, email, password_hash, full_name FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        if not user or not verify_password(password, user['password_hash']):
            return {"error": "Invalid email or password"}, 401

        session['user_id'] = user['id']
        session['email'] = user['email']
        session['full_name'] = user['full_name']
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "full_name": user['full_name']
            }
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()


def logout_user():
    session.clear()
    return {"success": True, "message": "Logged out"}, 200


def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, email, full_name FROM users WHERE id = %s",
            (session['user_id'],)
        )
        return cursor.fetchone()
    except:
        return None
    finally:
        conn.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


def add_business(user_id, business_name, shortcode, shortcode_type):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO businesses (user_id, business_name, shortcode, shortcode_type)
            VALUES (%s, %s, %s, %s)
        """, (user_id, business_name, shortcode, shortcode_type))
        conn.commit()
        return {"success": True, "business_id": cursor.lastrowid, "message": "Business added"}, 201
    except mysql.connector.IntegrityError:
        return {"error": "Shortcode already registered for this account"}, 409
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        conn.close()


def get_user_businesses(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, business_name, shortcode, shortcode_type, is_active, created_at
            FROM businesses WHERE user_id = %s ORDER BY created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()