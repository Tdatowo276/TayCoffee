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

def get_db_connection():
    """Tạo hoặc lấy một kết nối từ pool."""
    global _connection_pool
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
        except Exception as e:
            print(f"Lỗi khi khởi tạo Connection Pool: {e}")
            raise e
    
    return _connection_pool.getconn()

def release_db_connection(conn):
    """Trả kết nối về cho pool."""
    global _connection_pool
    if _connection_pool and conn:
        _connection_pool.putconn(conn)

def execute_query(query, params=None, fetch=False):
    """Hàm tiện ích để thực thi câu lệnh SQL."""
    conn = get_db_connection()
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
        conn.rollback()
        print(f"Lỗi thực thi SQL: {e}")
        raise e
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
