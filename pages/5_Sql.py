import streamlit as st
import pandas as pd
from Database import get_connection

# ── Auth Guard ────────────────────────────────────────────────────────────────
if 'role' not in st.session_state:
    st.switch_page("Login.py")

role      = st.session_state['role']
branch_id = st.session_state['branch_id']

# ✅ Restrict to Super Admin only
if role != 'Super Admin':
    st.warning("⛔ Access denied. This page is for Super Admins only.")
    st.stop()

st.title("🔍 SQL Queries")
st.markdown("---")
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Query Runner ──────────────────────────────────────────────────────────────
def run_query(query, params=None):
    conn = get_connection()
    try:
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df

# ── Predefined Queries ────────────────────────────────────────────────────────
queries = {
    "Total Sales Per Branch": """
        SELECT b.branch_name,
               COUNT(cs.sale_id)        as total_sales,
               SUM(cs.gross_sales)      as total_gross,
               SUM(cs.received_amount)  as total_received,
               SUM(cs.pending_amount)   as total_pending
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        GROUP BY b.branch_name
        ORDER BY total_gross DESC
    """,

    "Pending Payments by Customer": """
        SELECT cs.name,
               b.branch_name,
               cs.product_name,
               cs.gross_sales,
               cs.received_amount,
               cs.pending_amount,
               cs.status
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        WHERE cs.status = 'Open'
        ORDER BY cs.pending_amount DESC
    """,

    "Payment Method Summary": """
        SELECT payment_method,
               COUNT(*)          as total_transactions,
               SUM(amount_paid)  as total_amount
        FROM payment_splits
        GROUP BY payment_method
        ORDER BY total_amount DESC
    """,

    "Top 10 Highest Sales": """
        SELECT cs.name,
               b.branch_name,
               cs.product_name,
               cs.gross_sales,
               cs.date
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        ORDER BY cs.gross_sales DESC
        LIMIT 10
    """,

    "Monthly Sales Summary": """
        SELECT strftime('%Y-%m', date)  as month,
               COUNT(*)                 as total_sales,
               SUM(gross_sales)         as total_gross,
               SUM(received_amount)     as total_received
        FROM customer_sales
        GROUP BY month
        ORDER BY month
    """,

    "Branch Performance Summary": """
        SELECT b.branch_name,
               COUNT(cs.sale_id)        as total_sales,
               SUM(cs.gross_sales)      as total_gross,
               SUM(cs.received_amount)  as total_received,
               SUM(cs.pending_amount)   as total_pending,
               ROUND(SUM(cs.pending_amount) * 100.0 / SUM(cs.gross_sales), 2) as pending_percentage
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        GROUP BY b.branch_name
    """
}

# ── Query Selector ────────────────────────────────────────────────────────────
st.subheader("📋 Select a Query to Run")

selected_query = st.selectbox("Choose a query", list(queries.keys()))

with st.expander("👀 View SQL Code"):
    st.code(queries[selected_query], language='sql')

# ── Run Query ─────────────────────────────────────────────────────────────────
if st.button("▶️ Run Query", type='primary'):
    with st.spinner("Running query..."):
        result = run_query(queries[selected_query])

        if result.empty:
            st.warning("No results found!")
        else:
            st.success(f"✅ Query returned {len(result)} rows")
            st.dataframe(result, use_container_width=True)  # ✅ fixed
            
            
            