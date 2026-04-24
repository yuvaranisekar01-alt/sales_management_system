import os
import sqlite3
import pandas as pd
from Database import get_connection, create_tables

# ── STEP 1: Delete old database ───────────────────────────────────────────────
db_path = 'sales_hub.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print("🗑️ Old database deleted")

# ── STEP 2: Create tables properly with AUTOINCREMENT ────────────────────────
create_tables()
conn = get_connection()

# ── STEP 3: Read CSVs ─────────────────────────────────────────────────────────
branches       = pd.read_csv('branches.csv',       encoding="utf-8-sig")
customer_sales = pd.read_csv('customer_sales.csv', encoding="utf-8-sig")
users          = pd.read_csv('users.csv',          encoding="utf-8-sig")
payment_splits = pd.read_csv('payment_splits.csv', encoding="utf-8-sig")

# ── STEP 4: Clean all dataframes ─────────────────────────────────────────────
def clean_df(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(
            lambda x: x.encode('utf-8', errors='ignore')
                       .decode('utf-8') if isinstance(x, str) else x
        )
    return df

branches       = clean_df(branches)
customer_sales = clean_df(customer_sales)
users          = clean_df(users)
payment_splits = clean_df(payment_splits)

# ── STEP 5: Calculate pending_amount ─────────────────────────────────────────
customer_sales['pending_amount'] = customer_sales['gross_sales'] - customer_sales['received_amount']

# ── STEP 6: Drop primary key columns so AUTOINCREMENT works ──────────────────
# ✅ Remove ID columns — SQLite will auto-assign them
branches       = branches.drop(columns=['branch_id'],   errors='ignore')
customer_sales = customer_sales.drop(columns=['sale_id'],  errors='ignore')
users          = users.drop(columns=['user_id'],         errors='ignore')
payment_splits = payment_splits.drop(columns=['payment_id'], errors='ignore')

# ── STEP 7: Insert using append — preserves AUTOINCREMENT structure ───────────
branches.to_sql('branches',             conn, if_exists='append', index=False)
customer_sales.to_sql('customer_sales', conn, if_exists='append', index=False)
users.to_sql('users',                   conn, if_exists='append', index=False)
payment_splits.to_sql('payment_splits', conn, if_exists='append', index=False)

print("✅ Branches imported:",       len(branches),       "rows")
print("✅ Customer Sales imported:",  len(customer_sales), "rows")
print("✅ Users imported:",           len(users),          "rows")
print("✅ Payment Splits imported:",  len(payment_splits), "rows")
print("🎉 All data imported successfully!")

conn.close()


