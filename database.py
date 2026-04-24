import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "sales_hub.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def clean_str(value):
    if isinstance(value, str):
        return value.encode('utf-8', errors='ignore').decode('utf-8')
    return value

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches(
            branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_name VARCHAR(100),
            branch_admin_name VARCHAR(100))
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_sales(
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INT,
            date DATE,
            name VARCHAR(100),
            mobile_number VARCHAR(100),
            product_name VARCHAR(30),
            gross_sales DECIMAL(12,2),
            received_amount DECIMAL(12,2) DEFAULT 0,
            pending_amount DECIMAL(12,2) DEFAULT 0,
            status TEXT CHECK(status IN ('Open', 'Close')),
            FOREIGN KEY (branch_id) REFERENCES branches(branch_id))
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100),
            password VARCHAR(100),
            branch_id INT,
            role TEXT NOT NULL CHECK(role IN ('Super Admin', 'Admin')),
            email VARCHAR(100),
            FOREIGN KEY (branch_id) REFERENCES branches(branch_id))
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_splits(
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INT,
            payment_date DATE,
            amount_paid DECIMAL(12,2),
            payment_method VARCHAR(50),
            FOREIGN KEY (sale_id) REFERENCES customer_sales(sale_id))
    """)

    # ── Triggers — update received_amount AND pending_amount ─────────────────
    cursor.executescript("""
        CREATE TRIGGER IF NOT EXISTS update_received_amount_insert
        AFTER INSERT ON payment_splits
        FOR EACH ROW
        BEGIN
            UPDATE customer_sales
            SET received_amount = received_amount + NEW.amount_paid,
                pending_amount  = gross_sales - (received_amount + NEW.amount_paid)
            WHERE sale_id = NEW.sale_id;
        END;

        CREATE TRIGGER IF NOT EXISTS update_received_amount_update
        AFTER UPDATE ON payment_splits
        FOR EACH ROW
        BEGIN
            UPDATE customer_sales
            SET received_amount = received_amount + (NEW.amount_paid - OLD.amount_paid),
                pending_amount  = gross_sales - (received_amount + (NEW.amount_paid - OLD.amount_paid))
            WHERE sale_id = NEW.sale_id;
        END;

        CREATE TRIGGER IF NOT EXISTS update_received_amount_delete
        AFTER DELETE ON payment_splits
        FOR EACH ROW
        BEGIN
            UPDATE customer_sales
            SET received_amount = received_amount - OLD.amount_paid,
                pending_amount  = gross_sales - (received_amount - OLD.amount_paid)
            WHERE sale_id = OLD.sale_id;
        END;
    """)

    conn.commit()
    conn.close()

# ── Fetch functions ───────────────────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_branches():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM branches", conn)
    conn.close()

     # ✅ Sanitize all string columns on read
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(
            lambda x: x.encode('utf-8', errors='ignore')
                       .decode('utf-8') if isinstance(x, str) else x
        )
    
    return df

@st.cache_data(ttl=1)
def get_customer_sales():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT cs.sale_id,
               cs.branch_id,
               cs.date,
               cs.name,
               cs.mobile_number,
               cs.product_name,
               cs.gross_sales,
               COALESCE(SUM(ps.amount_paid), 0)                  AS received_amount,
               cs.gross_sales - COALESCE(SUM(ps.amount_paid), 0) AS pending_amount,
               cs.status
        FROM customer_sales cs
        LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
        GROUP BY cs.sale_id
    """, conn)
    conn.close()

    # ✅ Sanitize all string columns on read
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(
            lambda x: x.encode('utf-8', errors='ignore')
                       .decode('utf-8') if isinstance(x, str) else x
        )
    
    return df


@st.cache_data(ttl=1)
def get_users():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM users", conn)
    conn.close()

     # ✅ Sanitize all string columns on read
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(
            lambda x: x.encode('utf-8', errors='ignore')
                       .decode('utf-8') if isinstance(x, str) else x
        )
    
    return df

@st.cache_data(ttl=1)
def get_payment_splits():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM payment_splits", conn)
    conn.close()
    # ✅ Sanitize all string columns on read
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(
            lambda x: x.encode('utf-8', errors='ignore')
                       .decode('utf-8') if isinstance(x, str) else x
        )
    

    return df

# ── Insert functions ──────────────────────────────────────────────────────────

def add_branch(branch_name, admin_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO branches(branch_name, branch_admin_name) VALUES (?, ?)",
                   (branch_name, admin_name))
    conn.commit()
    conn.close()

def add_sale(branch_id, date, name, mobile, product, gross_sales, received_amount, status):
    conn = get_connection()
    cursor = conn.cursor()
    pending_amount = gross_sales - received_amount
    cursor.execute("""
        INSERT INTO customer_sales(branch_id, date, name, mobile_number, product_name,
        gross_sales, received_amount, pending_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (int(branch_id), str(date), 
         clean_str(name),      # ✅
         clean_str(mobile),    # ✅
         clean_str(product),   # ✅
         float(gross_sales), float(received_amount),
         float(pending_amount), clean_str(status)))  # ✅
    conn.commit()
    conn.close()

def add_payment(sale_id, payment_date, amount_paid, payment_method):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payment_splits(sale_id, payment_date, amount_paid, payment_method)
        VALUES (?, ?, ?, ?)""",
        (int(sale_id), str(payment_date), 
         float(amount_paid), 
         clean_str(payment_method)))  # ✅
    conn.commit()
    conn.close()

def check_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                   (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def update_sale(sale_id, branch_id, date, name, mobile, product, gross_sales, received_amount, status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE customer_sales
            SET branch_id     = ?,
                date          = ?,
                name          = ?,
                mobile_number = ?,
                product_name  = ?,
                gross_sales   = ?,
                status        = ?
            WHERE sale_id = ?
        """, (int(branch_id), str(date),
              clean_str(name),      # ✅
              clean_str(mobile),    # ✅
              clean_str(product),   # ✅
              float(gross_sales), 
              clean_str(status),    # ✅
              int(sale_id)))
        conn.commit()
    except Exception as e:
        print(f"ERROR in update_sale: {e}")
        raise e
    finally:
        conn.close()

def delete_sale(sale_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payment_splits WHERE sale_id = ?", (sale_id,))
    cursor.execute("DELETE FROM customer_sales WHERE sale_id = ?", (sale_id,))
    conn.commit()
    conn.close()

def update_payment(payment_id, payment_date, amount_paid, payment_method):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_splits
        SET payment_date   = ?,
            amount_paid    = ?,
            payment_method = ?
        WHERE payment_id = ?
    """, (str(payment_date), 
          float(amount_paid), 
          clean_str(payment_method),  # ✅
          int(payment_id)))
    conn.commit()
    conn.close()


def delete_payment(payment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payment_splits WHERE payment_id = ?", (payment_id,))
    conn.commit()
    conn.close()

