import streamlit as st
import pandas as pd
from database import get_customer_sales, get_branches, add_payment, get_payment_splits


if 'role' not in st.session_state:
    st.switch_page("Login.py")
    
#get role and branch
role = st.session_state['role']
branch = st.session_state['branch_id']

st.title("💰 Payments")
st.markdown("---")
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

payments = get_payment_splits()
sales = get_customer_sales()
branches = get_branches()

if role == 'Admin':
   sales =  sales[sales['branch_id'] == branch]
   payments = payments[payments['sale_id'].isin(sales['sale_id'])]

st.subheader("🔍 Filter Payments")
col1,col2 = st.columns(2)
with col1:
    # Payment method filter
    method_options = ['All'] + list(payments['payment_method'].unique())
    selected_method = st.selectbox("💳 Payment Method", method_options)
    if selected_method != 'All':
        payments = payments[payments['payment_method'] == selected_method]
with col2:
    # Date filter
    if not payments.empty:
        payments['payment_date'] = pd.to_datetime(payments['payment_date'])
        min_date = payments['payment_date'].min()
        max_date = payments['payment_date'].max()
        date_range = st.date_input("📅 Date Range",   value=(min_date, max_date))
        if len(date_range) == 2:
            payments = payments[
                (payments['payment_date'] >= pd.Timestamp(date_range[0])) &
                (payments['payment_date'] <= pd.Timestamp(date_range[1]))]
st.markdown("---")
st.subheader("📊 Payment Summary")

col1, col2, col3 = st.columns(3)
total_paid = payments['amount_paid'].sum()
cash_total = payments[payments['payment_method'] == 'Cash']['amount_paid'].sum()
card_total = payments[payments['payment_method'] == 'Card']['amount_paid'].sum()
            
with col1:
    st.metric("💰 Total Payments", f"₹{total_paid:,.2f}")
with col2:
    st.metric("💵 Cash Payments", f"₹{cash_total:,.2f}")
with col3:
    st.metric("💳 Card Payments", f"₹{card_total:,.2f}")

st.markdown("---")
st.subheader("📋 Payment Records")
st.dataframe(payments, use_container_width=True)
st.write(f"Total Records: {len(payments)}")

st.markdown("---")
st.subheader("➕ Add New Payment")

with st.form("add_payment_form"):
    col1, col2 = st.columns(2)

    with col1:
        # Show only relevant sales
        sale_ids = sales['sale_id'].tolist()
        selected_sale_id = st.selectbox("🧾 Sale ID", sale_ids)
        payment_date = st.date_input("📅 Payment Date")

    with col2:
        amount_paid = st.number_input("💰 Amount Paid", min_value=0.0)
        payment_method = st.selectbox("💳 Payment Method", 
                                       ["Cash", "Card", "UPI"])

    submit = st.form_submit_button("Add Payment", use_container_width=True)

    if submit:
        if amount_paid <= 0:
            st.error("Please enter a valid amount!")
        else:
            add_payment(selected_sale_id, payment_date, 
                       amount_paid, payment_method)
            st.success("✅ Payment added successfully!")
            st.rerun()
# Reports button
if st.button(" View Payment Reports", type = 'primary'):
    st.switch_page("pages/4_Reports.py")