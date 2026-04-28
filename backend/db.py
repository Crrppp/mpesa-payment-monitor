import mysql.connector
from mysql.connector import pooling
from config import Config

try:
    pool = pooling.MySQLConnectionPool(
        pool_name="mpesa_pool",
        pool_size=5,
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=True
    )
    USE_POOL = True
except:
    USE_POOL = False


def get_db():
    if USE_POOL:
        return pool.get_connection()
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


def test_connection():
    try:
        conn = get_db()
        conn.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)