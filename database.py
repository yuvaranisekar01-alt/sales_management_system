import sqlite3
import pandas as pd

DB_NAME = "sales_hub.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

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
            received_amount DECIMAL(12,2),
            pending_amount DECIMAL(12,2) GENERATED ALWAYS AS (gross_sales - received_amount) STORED,
            status TEXT CHECK(status IN ('Open', 'open', 'Close', 'close')),
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

    # Triggers
    cursor.executescript("""
        CREATE TRIGGER IF NOT EXISTS update_received_amount_insert
        AFTER INSERT ON payment_splits
        FOR EACH ROW
        BEGIN
            UPDATE customer_sales
            SET received_amount = received_amount + NEW.amount_paid
            WHERE sale_id = NEW.sale_id;
        END;

        CREATE TRIGGER IF NOT EXISTS update_received_amount_update
        AFTER UPDATE ON payment_splits
        FOR EACH ROW
        BEGIN
            UPDATE customer_sales
            SET received_amount = received_amount + (NEW.amount_paid - OLD.amount_paid)
            WHERE sale_id = NEW.sale_id;
        END;

        CREATE TRIGGER IF NOT EXISTS update_received_amount_delete
        AFTER DELETE ON payment_splits
        FOR EACH ROW
        BEGIN
            UPDATE customer_sales
            SET received_amount = received_amount - OLD.amount_paid
            WHERE sale_id = OLD.sale_id;
        END;
    """)

    conn.commit()
    conn.close()

# --- Fetch functions ---

def get_branches():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM branches", conn)
    conn.close()
    return df

def get_customer_sales():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM customer_sales", conn)
    conn.close()
    return df

def get_users():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM users", conn)
    conn.close()
    return df

def get_payment_splits():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM payment_splits", conn)
    conn.close()
    return df

# --- Insert functions ---

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
    cursor.execute("""
        INSERT INTO customer_sales(branch_id, date, name, mobile_number, product_name,
        gross_sales, received_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (branch_id, date, name, mobile, product, gross_sales, received_amount, status))
    conn.commit()
    conn.close()

def add_payment(sale_id, payment_date, amount_paid, payment_method):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payment_splits(sale_id, payment_date, amount_paid, payment_method)
        VALUES (?, ?, ?, ?)""",
        (sale_id, payment_date, amount_paid, payment_method))
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
    cursor.execute("""
        UPDATE customer_sales
        SET branch_id = ?,
            date = ?,
            name = ?,
            mobile_number = ?,
            product_name = ?,
            gross_sales = ?,
            received_amount = ?,
            status = ?
        WHERE sale_id = ?
    """, (branch_id, date, name, mobile, product, gross_sales, received_amount, status, sale_id))
    conn.commit()
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
        SET payment_date = ?,
            amount_paid = ?,
            payment_method = ?
        WHERE payment_id = ?
    """, (payment_date, amount_paid, payment_method, payment_id))
    conn.commit()
    conn.close()

def delete_payment(payment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payment_splits WHERE payment_id = ?", (payment_id,))
    conn.commit()
    conn.close()