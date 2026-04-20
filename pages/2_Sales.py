import streamlit as st
import pandas as pd
from database import get_customer_sales, get_branches, add_sale, update_sale, delete_sale

if 'role' not in st.session_state:
    st.switch_page("Login.py")

role = st.session_state['role']
branch = st.session_state['branch_id']

# Session state for edit/delete
if 'edit_sale_id' not in st.session_state:
    st.session_state['edit_sale_id'] = None
if 'delete_confirm_id' not in st.session_state:
    st.session_state['delete_confirm_id'] = None

st.title("🧾 Sales")
st.markdown("---")

sales = get_customer_sales()
branches = get_branches()
sales['status'] = sales['status'].str.capitalize()

if role == 'Admin':
    sales = sales[sales['branch_id'] == branch]

st.subheader("🔍 Filter Sales")

col1, col2, col3 = st.columns(3)
with col1:
    if role == 'Super Admin':
        branch_names = ['All Branches'] + list(branches['branch_name'])
        selected_branch = st.selectbox("🏢 Branch", branch_names)
        if selected_branch != 'All Branches':
            branch_id_filter = branches[branches['branch_name'] == selected_branch]['branch_id'].values[0]
            sales = sales[sales['branch_id'] == branch_id_filter]
with col2:
    status_options = ['All', 'Open', 'Close']
    selected_status = st.selectbox("📋 Status", status_options)
    if selected_status != 'All':
        sales = sales[sales['status'] == selected_status]
with col3:
    products = ['All'] + list(sales['product_name'].unique())
    selected_product = st.selectbox("📦 Product", products)
    if selected_product != 'All':
        sales = sales[sales['product_name'] == selected_product]


st.markdown("---")
st.subheader("📋 Sales Records")
st.write(f"Total Records: {len(sales)}")

with st.expander("📂 Show Sales Records", expanded=False):
    if sales.empty:
        st.info("No records found.")
    else:
        # Table header
        header_cols = st.columns([1, 2, 2, 2, 2, 2, 2, 1, 1])
        for col, h in zip(header_cols, ["ID", "Customer", "Product", "Gross", "Received", "Pending", "Status", "✏️", "🗑️"]):
            col.markdown(f"**{h}**")

        st.markdown("---")

        # Table rows
        for _, row in sales.iterrows():
            sale_id = row['sale_id']
            cols    = st.columns([1, 2, 2, 2, 2, 2, 2, 1, 1])
            cols[0].write(sale_id)
            cols[1].write(row['name'])
            cols[2].write(row['product_name'])
            cols[3].write(f"₹{row['gross_sales']:,.2f}")
            cols[4].write(f"₹{row['received_amount']:,.2f}")
            cols[5].write(f"₹{row['pending_amount']:,.2f}")
            cols[6].write(row['status'])

            if cols[7].button("✏️", key=f"edit_{sale_id}"):
                st.session_state['edit_sale_id'] = sale_id
                st.session_state['delete_confirm_id'] = None

            if cols[8].button("🗑️", key=f"del_{sale_id}"):
                st.session_state['delete_confirm_id'] = sale_id
                st.session_state['edit_sale_id'] = None

st.write(f"Total Records: {len(sales)}")

# ── DELETE CONFIRMATION ──────────────────────────────────────────────────────
if st.session_state['delete_confirm_id']:
    del_id = st.session_state['delete_confirm_id']
    st.warning(f"⚠️ Are you sure you want to delete Sale ID **{del_id}**?")
    c1, c2 = st.columns(2)
    if c1.button("✅ Yes, Delete", type="primary"):
        delete_sale(del_id)
        st.session_state['delete_confirm_id'] = None
        st.success("Sale deleted successfully!")
        st.rerun()
    if c2.button("❌ Cancel"):
        st.session_state['delete_confirm_id'] = None
        st.rerun()

# ── EDIT FORM ────────────────────────────────────────────────────────────────
if st.session_state['edit_sale_id']:
    edit_id = st.session_state['edit_sale_id']
    sale_row = sales[sales['sale_id'] == edit_id]

    if sale_row.empty:
        st.warning("Sale not found (it may have been filtered out). Clear filters to edit.")
    else:
        s = sale_row.iloc[0]
        st.markdown("---")
        st.subheader(f"✏️ Edit Sale ID: {edit_id}")

        with st.form("edit_sale_form"):
            col1, col2 = st.columns(2)
            with col1:
                if role == 'Super Admin':
                    branch_options = branches['branch_name'].tolist()
                    default_branch = branches[branches['branch_id'] == s['branch_id']]['branch_name'].values
                    default_idx = branch_options.index(default_branch[0]) if len(default_branch) else 0
                    edit_branch_name = st.selectbox("🏢 Branch", branch_options, index=default_idx)
                    edit_branch_id = branches[branches['branch_name'] == edit_branch_name]['branch_id'].values[0]
                else:
                    edit_branch_id = s['branch_id']
                    st.text_input("Branch ID", value=edit_branch_id, disabled=True)

                edit_name = st.text_input("👤 Customer Name", value=s['name'])
                edit_mobile = st.text_input("📱 Mobile Number", value=s['mobile_number'])
                edit_product = st.text_input("📦 Product Name", value=s['product_name'])

            with col2:
                edit_date = st.date_input("📅 Date", value=pd.to_datetime(s['date']))
                edit_gross = st.number_input("💰 Gross Sales", min_value=0.0, value=float(s['gross_sales']))
                edit_received = st.number_input("✅ Received Amount", min_value=0.0, value=float(s['received_amount']))
                status_list = ["Open", "Close"]
                edit_status = st.selectbox("📋 Status", status_list,
                                           index=status_list.index(s['status']) if s['status'] in status_list else 0)

            c1, c2 = st.columns(2)
            save = c1.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
            cancel = c2.form_submit_button("❌ Cancel", use_container_width=True)

        if save:
            if not edit_name or not edit_mobile or not edit_product:
                st.error("Please fill all fields!")
            else:
                update_sale(edit_id, edit_branch_id, edit_date, edit_name,
                            edit_mobile, edit_product, edit_gross, edit_received, edit_status)
                st.session_state['edit_sale_id'] = None
                st.success("✅ Sale updated successfully!")
                st.rerun()

        if cancel:
            st.session_state['edit_sale_id'] = None
            st.rerun()

# ── ADD NEW SALE ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("➕ Add New Sale")

with st.form("add_sale_form"):
    col1, col2 = st.columns(2)
    with col1:
        if role == 'Super Admin':
            branch_options = branches['branch_name'].tolist()
            selected_branch_name = st.selectbox("🏢 Branch", branch_options)
            new_branch_id = branches[branches['branch_name'] == selected_branch_name]['branch_id'].values[0]
        else:
            new_branch_id = branch
            st.text_input("Branch ID", value=new_branch_id, disabled=True)
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
    if not new_name or not new_mobile or not new_product:
        st.error("Please fill all fields!")
    else:
        add_sale(new_branch_id, new_date, new_name, new_mobile,
                 new_product, new_gross, new_received, new_status)
        st.success("✅ Sale added successfully!")
        st.rerun()

if st.button("Go to Payments Page", type='primary'):
    st.switch_page("pages/3_Payments.py")
