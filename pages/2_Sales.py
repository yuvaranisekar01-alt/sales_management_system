import streamlit as st
import pandas as pd
from database import get_customer_sales, get_branches, add_sale

if 'role' not in st.session_state:
    st.switch_page("Login.py")

# Get role and branch
role = st.session_state['role']
branch = st.session_state['branch_id']

st.title("🧾 Sales")
st.markdown("---")

#load data
sales = get_customer_sales()
branches = get_branches()

# Fix status case
sales['status'] = sales['status'].str.capitalize()

# Filter based on role
if role == 'Admin':
    sales = sales[sales['branch_id'] == branch]

st.subheader("🔍 Filter Sales")
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
     # Branch filter for Super Admin only
    if role == 'Super Admin':
        branch_names = ['All Branches'] + list(branches['branch_name'])
        selected_branch = st.selectbox("🏢 Branch", branch_names)
        if selected_branch != 'All Branches':
            branch_id_filter = branches[branches['branch_name'] == selected_branch]['branch_id'].values[0]
            sales = sales[sales['branch_id'] == branch_id_filter]
with col2:
    # Status filter
    status_options = ['All', 'Open', 'Close']
    selected_status = st.selectbox("📋 Status", status_options)
    if selected_status != 'All':
        sales = sales[sales['status'] == selected_status]
with col3:
     # Product filter
    products = ['All'] + list(sales['product_name'].unique())
    selected_product = st.selectbox("📦 Product", products)
    if selected_product != 'All':
        sales = sales[sales['product_name'] == selected_product]

st.markdown("---")
st.subheader("📋 Sales Records")
st.dataframe(sales, use_container_width=True)
st.write(f"Total Records: {len(sales)}")

st.markdown("---")
st.subheader("➕ Add New Sale")

with st.form("add_sale_form"):
    col1, col2 = st.columns(2)

with col1:
        # Branch selection
        if role == 'Super Admin':
            branch_options = branches['branch_name'].tolist()
            selected_branch_name = st.selectbox("🏢 Branch", branch_options)
            new_branch_id = branches[branches['branch_name'] == selected_branch_name]['branch_id'].values[0]
        else:
            new_branch_id = st.text_input('branch_id')


with col2:
        new_date = st.date_input("📅 Date")
        new_gross = st.number_input("💰 Gross Sales", min_value=0.0)
        new_received = st.number_input("✅ Received Amount", min_value=0.0)
        new_status = st.selectbox("📋 Status", ["Open", "Close"])
        new_name = st.text_input("👤 Customer Name")
        new_mobile = st.text_input("📱 Mobile Number")
        new_product = st.text_input("📦 Product Name")

        submit = st.form_submit_button("Add Sale", use_container_width=True)

if submit:
        if new_name == "" or new_mobile == "" or new_product == "":
            st.error("Please fill all fields!")
        else:
            add_sale(new_branch_id, new_date, new_name, new_mobile,
                    new_product, new_gross, new_received, new_status)
            st.success("✅ Sale added successfully!")
            st.rerun()
#payment button         
if st.button("Go to Payments Page", type='primary') :
   st.switch_page("pages/3_Payments.py")


