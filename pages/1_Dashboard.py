import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from Database import get_customer_sales, get_branches, get_payment_splits

# ── Auth Guard ────────────────────────────────────────────────────────────────
if 'role' not in st.session_state:
    st.switch_page("Login.py")

role   = st.session_state['role']
branch = st.session_state['branch_id']

# ── Page Config ───────────────────────────────────────────────────────────────
st.title('📊 Sales Dashboard')
st.markdown('---')

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
sales     = get_customer_sales()
branches  = get_branches()
payments  = get_payment_splits()

sales['status'] = sales['status'].str.capitalize()

# ── Filter by Role ────────────────────────────────────────────────────────────
if role == 'Admin':
    sales    = sales[sales['branch_id'] == branch]
    payments = payments[payments['sale_id'].isin(sales['sale_id'])]

if role == 'Super Admin':
    branch_names    = ['All Branches'] + list(branches['branch_name'])
    selected_branch = st.sidebar.selectbox("🏢 Filter by Branch", branch_names)

    if selected_branch != 'All Branches':
        branch_id_filter = branches[branches['branch_name'] == selected_branch]['branch_id'].values[0]
        sales = sales[sales['branch_id'] == branch_id_filter]

# ── KPI Metrics ───────────────────────────────────────────────────────────────
total_sales      = sales['gross_sales'].sum()
total_received   = sales['received_amount'].sum()
total_pending    = total_sales - total_received
pending_pct      = (total_pending / total_sales) * 100 if total_sales > 0 else 0

st.subheader("📊 Financial KPI Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="💰 Total Sales",      value=f"₹{total_sales:,.2f}")
with col2:
    st.metric(label="✅ Received Amount",  value=f"₹{total_received:,.2f}")
with col3:
    st.metric(label="⏳ Pending Amount",   value=f"₹{total_pending:,.2f}")
with col4:
    st.metric(label="📉 Pending %",        value=f"{pending_pct:.1f}%")

st.markdown("---")

# ── Sales Status Chart ────────────────────────────────────────────────────────
st.subheader("📊 Sales Status Distribution")

status_count = sales['status'].value_counts()

# ✅ Map colors to status explicitly
color_map = {'Open': '#927FF0', 'Close': '#4CAF50'}
colors    = [color_map.get(s, '#cccccc') for s in status_count.index]

fig, ax = plt.subplots()
ax.bar(status_count.index, status_count.values, color=colors, width=0.4)
ax.set_title('Sales Status Distribution')
ax.set_xlabel('Status')
ax.set_ylabel('Count')

st.pyplot(fig)

st.markdown("---")

# ── Navigation ────────────────────────────────────────────────────────────────
if st.button("Go to Sales Page", type='primary'):
    st.switch_page("pages/2_Sales.py")


