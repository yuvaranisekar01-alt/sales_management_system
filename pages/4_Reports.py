import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from Database import get_customer_sales, get_branches, get_payment_splits

# ── Auth Guard ────────────────────────────────────────────────────────────────
if 'role' not in st.session_state:
    st.switch_page("Login.py")

role      = st.session_state['role']
branch_id = st.session_state['branch_id']

st.title("📊 Reports & Analytics")
st.markdown("---")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
sales    = get_customer_sales()
branches = get_branches()
payments = get_payment_splits()

sales['status'] = sales['status'].str.capitalize()

# ── Role Filter ───────────────────────────────────────────────────────────────
if role == 'Admin':
    sales    = sales[sales['branch_id'] == branch_id]
    payments = payments[payments['sale_id'].isin(sales['sale_id'])]

# ── Branch Wise Sales (Super Admin only) ──────────────────────────────────────
if role == 'Super Admin':                           # ✅ hide for Admin
    st.subheader("🏢 Branch Wise Sales Comparison")

    branch_sales   = sales.merge(branches, on='branch_id', how='left')
    branch_summary = branch_sales.groupby('branch_name')['gross_sales'].sum().reset_index()

    # ✅ Dynamic colors
    palette = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#FF5722']
    colors  = palette[:len(branch_summary)]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(branch_summary['branch_name'],
           branch_summary['gross_sales'],
           color=colors,
           width=0.4)
    ax.set_title('Branch Wise Sales Comparison')
    ax.set_xlabel('Branch')
    ax.set_ylabel('Total Sales (₹)')
    st.pyplot(fig)
    st.markdown("---")

# ── Received vs Pending ───────────────────────────────────────────────────────
st.subheader("✅ Received vs Pending Amount")

total_received = sales['received_amount'].sum()
total_pending  = sales['pending_amount'].sum()

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(['Received', 'Pending'],
           [total_received, total_pending],
           color=['#4CAF50', '#FF6B6B'],
           width=0.4)
    ax.set_title('Received vs Pending')
    ax.set_ylabel('Amount (₹)')
    st.pyplot(fig)

with col2:
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie([total_received, total_pending],
            labels=['Received', 'Pending'],
            colors=['#4CAF50', '#FF6B6B'],
            autopct='%1.1f%%',
            startangle=90)
    ax2.set_title('Collection %')
    st.pyplot(fig2)

st.markdown("---")

# ── Payment Method Analysis ───────────────────────────────────────────────────
st.subheader("💳 Payment Method Analysis")

payment_summary = payments.groupby('payment_method')['amount_paid'].sum().reset_index()

# ✅ Dynamic colors for payment methods too
palette2  = ['#4CAF50', '#2196F3', '#FF9800']
colors2   = palette2[:len(payment_summary)]

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(payment_summary['amount_paid'],
           labels=payment_summary['payment_method'],
           autopct='%1.1f%%',
           colors=colors2,
           startangle=90)
    ax.set_title('Payment Method Distribution')
    st.pyplot(fig)

with col2:
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.bar(payment_summary['payment_method'],
            payment_summary['amount_paid'],
            color=colors2,
            width=0.4)
    ax2.set_title('Payment Method Amounts')
    ax2.set_xlabel('Payment Method')
    ax2.set_ylabel('Total Amount (₹)')
    st.pyplot(fig2)

st.markdown("---")

# ── Monthly Sales Trend ───────────────────────────────────────────────────────
st.subheader("📈 Sales Trend Over Time")

sales['date']  = pd.to_datetime(sales['date'])
sales['month'] = sales['date'].dt.to_period('M').astype(str)

monthly_sales  = sales.groupby('month')['gross_sales'].sum().reset_index()
monthly_sales  = monthly_sales.sort_values('month')

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(monthly_sales['month'],
        monthly_sales['gross_sales'],
        color='#2196F3',
        marker='o',
        linewidth=2,
        markersize=6)
ax.set_title('Monthly Sales Trend')
ax.set_xlabel('Month')
ax.set_ylabel('Total Sales (₹)')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig)

st.markdown("---")

# ── Navigation ────────────────────────────────────────────────────────────────
if st.button('View SQL Page', type='primary'):
    st.switch_page("pages/5_Sql.py")
    