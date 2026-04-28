import psycopg2
import psycopg2.pool
from config import Config

# SSL mode required for Aiven
DATABASE_URL = (
    f"host={Config.DB_HOST} port={Config.DB_PORT} "
    f"dbname={Config.DB_NAME} user={Config.DB_USER} "
    f"password={Config.DB_PASSWORD} sslmode=require"
)

try:
    pool = psycopg2.pool.ThreadedConnectionPool(1, 5, DATABASE_URL)
    USE_POOL = True
except Exception as e:
    print(f"⚠️ Could not create connection pool: {e}")
    USE_POOL = False


def get_db():
    """Get a database connection."""
    if USE_POOL:
        return pool.getconn()
    return psycopg2.connect(DATABASE_URL)


def return_db(conn):
    """Return connection to pool, or close it."""
    if USE_POOL:
        pool.putconn(conn)
    else:
        conn.close()


def test_connection():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        return_db(conn)
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)