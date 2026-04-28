from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import psycopg2.errors
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import get_db, return_db, test_connection
from security import encrypt_phone, decrypt_phone, hash_phone
from auth import (
    signup_user, login_user, logout_user,
    get_current_user, login_required,
    add_business, get_user_businesses
)

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False

CORS(app,
     origins=[
         "http://localhost:8501",
         "http://127.0.0.1:8501",
         "https://*.render.com",
         "https://*.onrender.com"
     ],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


def init_db():
    """Create tables if they don't exist (idempotent)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "database", "schema.sql"
        )
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Database tables verified/created.")
    except Exception as e:
        print(f"⚠️ Schema init error (may already exist): {e}")
        conn.rollback()
    finally:
        cursor.close()
        return_db(conn)


@app.route("/api/signup", methods=["POST", "OPTIONS"])
def signup():
    if request.method == "OPTIONS":
        return "", 200
    data = request.json
    result, status = signup_user(
        data.get("email"),
        data.get("password"),
        data.get("full_name", "")
    )
    return jsonify(result), status


@app.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200
    data = request.json
    result, status = login_user(data.get("email"), data.get("password"))
    return jsonify(result), status


@app.route("/api/logout", methods=["POST"])
def logout():
    result, status = logout_user()
    return jsonify(result), status


@app.route("/api/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(user), 200


@app.route("/api/businesses", methods=["GET"])
@login_required
def list_businesses():
    user = get_current_user()
    businesses = get_user_businesses(user['id'])
    return jsonify(businesses), 200


@app.route("/api/businesses", methods=["POST"])
@login_required
def create_business():
    user = get_current_user()
    data = request.json
    result, status = add_business(
        user['id'],
        data.get("business_name"),
        data.get("shortcode"),
        data.get("shortcode_type", "till")
    )
    return jsonify(result), status


@app.route("/api/payments", methods=["GET"])
@login_required
def get_payments():
    user = get_current_user()
    business_id = request.args.get("business_id")
    search = request.args.get("search", "")

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT p.id, p.business_id, p.phone_encrypted, p.amount,
               p.mpesa_code, p.transaction_time, p.created_at,
               b.business_name
        FROM payments p
        JOIN businesses b ON p.business_id = b.id
        WHERE b.user_id = %s
    """
    params = [user['id']]

    if business_id:
        query += " AND p.business_id = %s"
        params.append(business_id)

    if search:
        search_hash = hash_phone(search)
        query += " AND p.phone_hash = %s"
        params.append(search_hash)

    query += " ORDER BY p.transaction_time DESC LIMIT 500"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    payments = []
    for row in rows:
        p = {
            "id": row[0],
            "business_id": row[1],
            "phone_encrypted": row[2],
            "amount": float(row[3]),
            "mpesa_code": row[4],
            "transaction_time": row[5].isoformat(),
            "created_at": row[6].isoformat(),
            "business_name": row[7]
        }
        try:
            full_phone = decrypt_phone(p['phone_encrypted'])
            p['phone_masked'] = f"{full_phone[:4]}****{full_phone[-3:]}" if len(full_phone) >= 10 else "****"
        except:
            p['phone_masked'] = "****"
        del p['phone_encrypted']
        payments.append(p)

    cursor.close()
    return_db(conn)
    return jsonify(payments), 200


@app.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    user = get_current_user()
    business_id = request.args.get("business_id")

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            COUNT(*) as total_transactions,
            COALESCE(SUM(amount), 0) as total_amount,
            DATE(transaction_time) as date
        FROM payments p
        JOIN businesses b ON p.business_id = b.id
        WHERE b.user_id = %s
    """
    params = [user['id']]

    if business_id:
        query += " AND p.business_id = %s"
        params.append(business_id)

    query += " GROUP BY DATE(transaction_time) ORDER BY date DESC LIMIT 30"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    stats = [{"total_transactions": r[0], "total_amount": float(r[1]), "date": str(r[2])} for r in rows]
    cursor.close()
    return_db(conn)
    return jsonify(stats), 200


def get_business_by_shortcode(shortcode):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, business_name FROM businesses WHERE shortcode = %s AND is_active = TRUE",
        (shortcode,)
    )
    row = cursor.fetchone()
    business = {"id": row[0], "user_id": row[1], "business_name": row[2]} if row else None
    cursor.close()
    return_db(conn)
    return business


@app.route("/confirmation", methods=["POST"])
def mpesa_confirmation():
    data = request.json
    print(f"📨 Payment received: {data}")

    shortcode = data.get("BusinessShortCode")
    business = get_business_by_shortcode(shortcode)

    if not business:
        print(f"⚠️ Unknown shortcode: {shortcode}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Unknown business"}), 200

    conn = get_db()
    cursor = conn.cursor()

    try:
        phone = data.get("MSISDN", "")
        amount = data.get("TransAmount", 0)
        code = data.get("TransID", "")
        time_str = data.get("TransTime", "")

        if len(time_str) == 14:
            trans_time = datetime.strptime(time_str, "%Y%m%d%H%M%S")
        else:
            trans_time = datetime.now()

        phone_encrypted = encrypt_phone(phone)
        phone_hash = hash_phone(phone)

        cursor.execute("""
            INSERT INTO payments
            (business_id, phone_encrypted, phone_hash, amount, mpesa_code, transaction_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (business['id'], phone_encrypted, phone_hash, amount, code, trans_time))

        conn.commit()
        print(f"✅ Payment saved: {business['business_name']} - KES {amount}")

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print(f"⚠️ Duplicate transaction: {code}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        return_db(conn)

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@app.route("/validation", methods=["POST"])
def mpesa_validation():
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@app.route("/health", methods=["GET"])
def health():
    db_ok, db_msg = test_connection()
    return jsonify({
        "status": "healthy" if db_ok else "unhealthy",
        "database": db_msg,
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == "__main__":
    print("🚀 Starting M-Pesa Payment Monitor Backend...")
    print(f"📍 Database: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")

    # Auto-create tables on startup
    init_db()

    db_ok, db_msg = test_connection()
    if db_ok:
        print(f"✅ Database connected: {db_msg}")
    else:
        print(f"⚠️ Database warning: {db_msg}")
    app.run(host="0.0.0.0", port=5000, debug=True)