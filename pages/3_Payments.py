import streamlit as st
import pandas as pd
from Database import (get_customer_sales, get_branches, add_payment,
                      get_payment_splits, update_payment, delete_payment)

# ── Auth Guard ────────────────────────────────────────────────────────────────
if 'role' not in st.session_state:
    st.switch_page("Login.py")

role   = st.session_state['role']
branch = st.session_state['branch_id']

# ── Session State ─────────────────────────────────────────────────────────────
if 'edit_payment_id' not in st.session_state:
    st.session_state['edit_payment_id'] = None
if 'delete_confirm_payment_id' not in st.session_state:
    st.session_state['delete_confirm_payment_id'] = None

st.title("💰 Payments")
st.markdown("---")

# ── Load Data ─────────────────────────────────────────────────────────────────
payments = get_payment_splits()
sales    = get_customer_sales()
branches = get_branches()

sales['status'] = sales['status'].str.capitalize()  # ✅ capitalize once here only

# ── Role Filter ───────────────────────────────────────────────────────────────
if role == 'Admin':
    sales    = sales[sales['branch_id'] == branch]
    payments = payments[payments['sale_id'].isin(sales['sale_id'])]

# ── Filters ───────────────────────────────────────────────────────────────────
st.subheader("🔍 Filter Payments")
col1, col2, col3 = st.columns(3)

with col1:
    if role == 'Super Admin':
        branch_names    = ['All Branches'] + list(branches['branch_name'])
        selected_branch = st.selectbox("🏢 Branch", branch_names)
        if selected_branch != 'All Branches':
            bid             = branches[branches['branch_name'] == selected_branch]['branch_id'].values[0]
            branch_sale_ids = sales[sales['branch_id'] == bid]['sale_id']
            payments        = payments[payments['sale_id'].isin(branch_sale_ids)]

with col2:
    method_options  = ['All'] + list(payments['payment_method'].unique())
    selected_method = st.selectbox("💳 Payment Method", method_options)
    if selected_method != 'All':
        payments = payments[payments['payment_method'] == selected_method]

with col3:
    if not payments.empty:
        payments['payment_date'] = pd.to_datetime(payments['payment_date'])
        min_date   = payments['payment_date'].min()
        max_date   = payments['payment_date'].max()
        date_range = st.date_input("📅 Date Range", value=(min_date, max_date))
        if len(date_range) == 2:
            payments = payments[
                (payments['payment_date'] >= pd.Timestamp(date_range[0])) &
                (payments['payment_date'] <= pd.Timestamp(date_range[1]))
            ]

st.markdown("---")

# ── Summary Metrics ───────────────────────────────────────────────────────────
st.subheader("📊 Payment Summary")
col1, col2, col3, col4 = st.columns(4)

total_paid = payments['amount_paid'].sum()
cash_total = payments[payments['payment_method'] == 'Cash']['amount_paid'].sum()
card_total = payments[payments['payment_method'] == 'Card']['amount_paid'].sum()
upi_total  = payments[payments['payment_method'] == 'UPI']['amount_paid'].sum()

with col1:
    st.metric("💰 Total Payments", f"₹{total_paid:,.2f}")
with col2:
    st.metric("💵 Cash",           f"₹{cash_total:,.2f}")
with col3:
    st.metric("💳 Card",           f"₹{card_total:,.2f}")
with col4:
    st.metric("📲 UPI",            f"₹{upi_total:,.2f}")

st.markdown("---")

# ── Payment Records ───────────────────────────────────────────────────────────
st.subheader("📋 Payment Records")
st.write(f"Total Records: {len(payments)}")

if payments.empty:
    st.info("No payment records found.")
else:
    with st.expander("📂 Show Payment Records", expanded=False):
        display_df = payments[['payment_id', 'sale_id', 'payment_date',
                                'amount_paid', 'payment_method']].copy()
        display_df.columns = ['Pay ID', 'Sale ID', 'Date', 'Amount (₹)', 'Method']
        display_df['Date']       = display_df['Date'].astype(str).str[:10]
        display_df['Amount (₹)'] = display_df['Amount (₹)'].apply(lambda x: f"₹{x:,.2f}")

        st.dataframe(display_df, use_container_width=True, height=300)
        st.markdown("---")

        pay_ids      = payments['payment_id'].tolist()
        selected_pid = st.selectbox("Select Payment ID to Edit or Delete", options=pay_ids)

        col1, col2 = st.columns(2)
        if col1.button("✏️ Edit Selected",   key="edit_payment_btn"):
            st.session_state['edit_payment_id']           = selected_pid
            st.session_state['delete_confirm_payment_id'] = None
        if col2.button("🗑️ Delete Selected", key="delete_payment_btn"):
            st.session_state['delete_confirm_payment_id'] = selected_pid
            st.session_state['edit_payment_id']           = None

# ── Delete Confirmation ───────────────────────────────────────────────────────
if st.session_state['delete_confirm_payment_id']:
    del_id = st.session_state['delete_confirm_payment_id']
    st.warning(f"⚠️ Are you sure you want to delete Payment ID **{del_id}**? "
               f"This will also reduce the received amount on the linked sale.")
    c1, c2 = st.columns(2)
    if c1.button("✅ Yes, Delete", type="primary"):
        delete_payment(del_id)
        st.session_state['delete_confirm_payment_id'] = None
        st.success("Payment deleted successfully!")
        st.rerun()
    if c2.button("❌ Cancel"):
        st.session_state['delete_confirm_payment_id'] = None
        st.cache_data.clear() 
        st.rerun()

# ── Edit Form ─────────────────────────────────────────────────────────────────
if st.session_state['edit_payment_id']:
    edit_id      = st.session_state['edit_payment_id']
    all_payments = get_payment_splits()
    pay_row      = all_payments[all_payments['payment_id'] == edit_id]

    if pay_row.empty:
        st.warning("Payment not found.")
    else:
        p = pay_row.iloc[0]
        st.markdown("---")
        st.subheader(f"✏️ Edit Payment ID: {edit_id}")

        linked_sale = sales[sales['sale_id'] == p['sale_id']]
        if not linked_sale.empty:
            current_pending = float(linked_sale.iloc[0]['pending_amount']) + float(p['amount_paid'])
            st.info(f"Remaining balance on Sale #{p['sale_id']} (excluding this payment): ₹{current_pending:,.2f}")

        with st.form("edit_payment_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_date   = st.date_input("📅 Payment Date",
                                            value=pd.to_datetime(p['payment_date']))
                edit_amount = st.number_input("💰 Amount Paid", min_value=0.0,
                                              value=float(p['amount_paid']))
            with col2:
                methods     = ["Cash", "Card", "UPI"]
                edit_method = st.selectbox("💳 Payment Method", methods,
                                           index=methods.index(p['payment_method'])
                                           if p['payment_method'] in methods else 0)

            c1, c2 = st.columns(2)
            save   = c1.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
            cancel = c2.form_submit_button("❌ Cancel",        use_container_width=True)

            if save:        # ✅ inside form
                if edit_amount <= 0:
                    st.error("Amount must be greater than 0!")
                elif not linked_sale.empty and edit_amount > current_pending:
                    st.error(f"Amount exceeds pending balance of ₹{current_pending:,.2f}!")
                else:
                    update_payment(edit_id, edit_date, edit_amount, edit_method)
                    st.session_state['edit_payment_id'] = None
                    st.success("✅ Payment updated successfully!")
                    st.cache_data.clear() 
                    st.rerun()

            if cancel:      # ✅ inside form
                st.session_state['edit_payment_id'] = None
                st.cache_data.clear() 
                st.rerun()

st.markdown("---")

# ── Add New Payment ───────────────────────────────────────────────────────────
st.subheader("➕ Add New Payment")

# ✅ Descriptive label
sales['label'] = (sales['sale_id'].astype(str) + ' | ' +
                  sales['name'] + ' | ₹' +
                  sales['pending_amount'].apply(lambda x: f"{x:,.2f}"))

open_sales = sales[sales['status'] == 'Open']  # ✅ no redundant capitalize

if open_sales.empty:
    st.info("No open sales available for payment.")
else:
    with st.form("add_payment_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_label   = st.selectbox("🧾 Sale", open_sales['label'].tolist())
            selected_sale_id = open_sales[open_sales['label'] == selected_label]['sale_id'].values[0]
            pending          = open_sales[open_sales['sale_id'] == selected_sale_id]['pending_amount'].values[0]
            payment_date     = st.date_input("📅 Payment Date")
        with col2:
            amount_paid    = st.number_input("💰 Amount Paid", min_value=0.0, max_value=float(pending))
            payment_method = st.selectbox("💳 Payment Method", ["Cash", "Card", "UPI"])
            st.caption(f"⚠️ Max payable: ₹{pending:,.2f}")

        submit = st.form_submit_button("Add Payment", use_container_width=True)

        if submit:      # ✅ inside form
            if amount_paid <= 0:
                st.error("Please enter a valid amount!")
            elif amount_paid > pending:
                st.error(f"Amount exceeds pending balance of ₹{pending:,.2f}!")
            else:
                add_payment(selected_sale_id, payment_date, amount_paid, payment_method)
                st.success("✅ Payment added successfully!")
                st.cache_data.clear() 
                st.rerun()

# ── Navigation ────────────────────────────────────────────────────────────────
if st.button("View Payment Reports", type='primary'):
    st.switch_page("pages/4_Reports.py")
    