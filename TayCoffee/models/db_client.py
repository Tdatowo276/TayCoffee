import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

# Lấy các biến môi trường cho Database cục bộ
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'tay_coffee')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'password')
DB_PORT = os.getenv('DB_PORT', '5432')

_connection_pool = None
_db_available = True

def get_db_connection():
    """Tạo hoặc lấy một kết nối từ pool."""
    global _connection_pool, _db_available
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1, 20,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME
            )
            _db_available = True
        except Exception as e:
            print(f"⚠️ Database không khả dụng: {e}")
            _db_available = False
            return None
    
    try:
        return _connection_pool.getconn()
    except Exception as e:
        print(f"⚠️ Lỗi lấy connection từ pool: {e}")
        _db_available = False
        return None

def release_db_connection(conn):
    """Trả kết nối về cho pool."""
    global _connection_pool
    if _connection_pool and conn:
        try:
            _connection_pool.putconn(conn)
        except:
            pass

def execute_query(query, params=None, fetch=False):
    """Hàm tiện ích để thực thi câu lệnh SQL. Trả về empty data nếu database không available."""
    conn = get_db_connection()
    if conn is None:
        print(f"⚠️ Database không khả dụng, trả về dữ liệu trống")
        return [] if fetch else False
    
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                # Trả về kết quả dưới dạng danh sách các dict
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
            conn.commit()
            return True
    except Exception as e:
        print(f"⚠️ Lỗi thực thi SQL: {e}")
        if fetch:
            return []
        return False
    finally:
        release_db_connection(conn)

def execute_insert_returning(query, params=None):
    """Thực thi INSERT và trả về row vừa chèn."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            columns = [desc[0] for desc in cur.description]
            conn.commit()
            return dict(zip(columns, result)) if result else None
    except Exception as e:
        conn.rollback()
        print(f"Lỗi thực thi INSERT: {e}")
        raise e
    finally:
        release_db_connection(conn)
