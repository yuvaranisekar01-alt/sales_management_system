import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import numpy as np
from database import get_customer_sales, get_branches , get_payment_splits


if 'role' not in st.session_state:
    st.switch_page("Login.py")

role = st.session_state['role']
branch = st.session_state['branch_id']

st.title('📊 Sales Dashboard')
st.markdown('------')

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

sales = get_customer_sales()
branches = get_branches()
payments = get_payment_splits()

sales['status'] = sales['status'].str.capitalize()

#filter branches based on role
if role == 'Admin':
    sales = sales[sales['branch_id'] == branch]
    payments = payments[payments['sale_id'].isin(sales['sale_id'])]

# Only show filter to Super Admin
if role == 'Super Admin':
    branch_names = ['All Branches'] + list(branches['branch_name'])
    selected_branch = st.sidebar.selectbox("🏢 Filter by Branch", branch_names)
    
    # Filter sales based on selection
    if selected_branch != 'All Branches':
        branch_id_filter = branches[branches['branch_name'] == selected_branch]['branch_id'].values[0]
        sales = sales[sales['branch_id'] == branch_id_filter]

total_sales = sales['gross_sales'].sum()
total_received = sales['received_amount'].sum()
total_pending = total_sales - total_received
pending_percentage = (total_pending / total_sales) * 100 if total_sales > 0 else 0


st.subheader("📊 Financial KPI Summary")
col1, col2, col3,col4 = st.columns(4)



with col1:
    st.metric(label="💰 Total Sales", value=f"₹{total_sales/10000:,.2f}")

with col2:
    st.metric(label="✅ Received Amount", value=f"₹{total_received/10000:,.2f}")

with col3:
    st.metric(label="⏳ Pending Amount", value=f"₹{total_pending/10000:,.2f}")

with col4:
    st.metric(label="📉 Pending %", value=f"{pending_percentage:.1f}%")

st.markdown("---")
st.subheader("📊 Sales Status")

# Count open vs closed sales
st.write(sales['status'].unique())
status_count = sales['status'].value_counts()

fig, ax = plt.subplots()

ax.bar(status_count.index, 
       status_count.values, 
       color=["#927FF0", '#4CAF50'],
       width=0.4)

ax.set_title('Sales Status Distribution')
ax.set_xlabel('Status')
ax.set_ylabel('Count')

st.pyplot(fig)

# sales button
if st.button("Go to Sales Page", type='primary'):
    st.switch_page("pages/2_Sales.py")