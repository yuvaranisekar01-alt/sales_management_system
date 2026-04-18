import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt 
import numpy as np
from database import get_customer_sales, get_branches , get_payment_splits

if 'role' not in st.session_state:
    st.switch_page("Login.py")

role = st.session_state['role']
branch_id = st.session_state['branch_id']

st.title("📊 Reports & Analytics")
st.markdown("---")
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Load data
sales = get_customer_sales()
branches = get_branches()
payments = get_payment_splits()

# Fix status
sales['status'] = sales['status'].str.capitalize()

# Filter for Admin
if role == 'Admin':
    sales = sales[sales['branch_id'] == branch_id]
    payments = payments[payments['sale_id'].isin(sales['sale_id'])]

st.subheader("🏢 Branch Wise Sales Comparison")
# Merge sales with branches to get branch names
branch_sales = sales.merge(branches, on='branch_id', how='left')

# Group by branch and sum gross sales
branch_summary = branch_sales.groupby('branch_name')['gross_sales'].sum().reset_index()

# Draw bar chart
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(branch_summary['branch_name'], 
       branch_summary['gross_sales'],
       color=['#4CAF50', '#2196F3', '#FF9800'],
       width=0.4)

ax.set_title('Branch Wise Sales Comparison')
ax.set_xlabel('Branch')
ax.set_ylabel('Total Sales (₹)')

st.pyplot(fig)

st.markdown("---")
st.subheader("✅ Received vs Pending Amount")

col1, col2 = st.columns(2)

# Calculate totals
total_received = sales['received_amount'].sum()
total_pending = sales['pending_amount'].sum()

with col1:
    # Bar chart comparing received vs pending
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(['Received', 'Pending'],
           [total_received, total_pending],
           color=['#4CAF50', '#FF6B6B'],
           width=0.4)
    ax.set_title('Received vs Pending')
    ax.set_ylabel('Amount (₹)')
    st.pyplot(fig)

with col2:
    # Pie chart showing percentage
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie([total_received, total_pending],
            labels=['Received', 'Pending'],
            colors=['#4CAF50', '#FF6B6B'],
            autopct='%1.1f%%',
            startangle=90)
    ax2.set_title('Collection %')
    st.pyplot(fig2)

st.markdown("---")
st.subheader("💳 Payment Method Analysis")

col1, col2 = st.columns(2)

# Group payments by method
payment_summary = payments.groupby('payment_method')['amount_paid'].sum().reset_index()

with col1:
    # Pie chart
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(payment_summary['amount_paid'],
           labels=payment_summary['payment_method'],
           autopct='%1.1f%%',
           colors=['#4CAF50', '#2196F3', '#FF9800'],
           startangle=90)
    ax.set_title('Payment Method Distribution')
    st.pyplot(fig)

with col2:
    # Bar chart
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.bar(payment_summary['payment_method'],
            payment_summary['amount_paid'],
            color=['#4CAF50', '#2196F3', '#FF9800'],
            width=0.4)
    ax2.set_title('Payment Method Amounts')
    ax2.set_xlabel('Payment Method')
    ax2.set_ylabel('Total Amount (₹)')
    st.pyplot(fig2)

st.markdown("---")
st.subheader("📈 Sales Trend Over Time")

# Convert date column to datetime
sales['date'] = pd.to_datetime(sales['date'])

# Group by month
sales['month'] = sales['date'].dt.to_period('M').astype(str)
monthly_sales = sales.groupby('month')['gross_sales'].sum().reset_index()
monthly_sales = monthly_sales.sort_values('month')

# Line chart
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

# sql query button
if st.button('View Sql page' , type= 'primary'): 
    st.switch_page("pages/5_Sql.py")
