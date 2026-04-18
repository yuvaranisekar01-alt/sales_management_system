import sqlite3
import pandas as pd
from database import get_connection, create_tables

# First create all tables
create_tables()

# Connect to database
conn = get_connection()

# Read your CSV files
branches = pd.read_csv('branches.csv')
customer_sales = pd.read_csv('customer_sales.csv')
users = pd.read_csv('users.csv')
payment_splits = pd.read_csv('payment_splits.csv')

# Import into SQLite tables
branches.to_sql('branches', conn, if_exists='append', index=False)
customer_sales.to_sql('customer_sales', conn, if_exists='append', index=False)
users.to_sql('users', conn, if_exists='append', index=False)
payment_splits.to_sql('payment_splits', conn, if_exists='append', index=False)

print("✅ Branches imported:", len(branches), "rows")
print("✅ Customer Sales imported:", len(customer_sales), "rows")
print("✅ Users imported:", len(users), "rows")
print("✅ Payment Splits imported:", len(payment_splits), "rows")
print("🎉 All data imported successfully!")

conn.close()
