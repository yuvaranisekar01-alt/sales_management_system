import streamlit as st
import pandas as pd
from database import (get_customer_sales, get_branches, add_payment,
                      get_payment_splits, update_payment, delete_payment)

if 'role' not in st.session_state:
    st.switch_page("Login.py")

role = st.session_state['role']
branch = st.session_state['branch_id']

# Session state for edit/delete
if 'edit_payment_id' not in st.session_state:
    st.session_state['edit_payment_id'] = None
if 'delete_confirm_payment_id' not in st.session_state:
    st.session_state['delete_confirm_payment_id'] = None

st.title("💰 Payments")
st.markdown("---")

payments = get_payment_splits()
sales    = get_customer_sales()
branches = get_branches()

# Role-based filter
if role == 'Admin':
    sales    = sales[sales['branch_id'] == branch]
    payments = payments[payments['sale_id'].isin(sales['sale_id'])]

# ── FILTERS ──────────────────────────────────────────────────────────────────
st.subheader("🔍 Filter Payments")
col1, col2, col3 = st.columns(3)

with col1:
    if role == 'Super Admin':
        branch_names = ['All Branches'] + list(branches['branch_name'])
        selected_branch = st.selectbox("🏢 Branch", branch_names)
        if selected_branch != 'All Branches':
            bid = branches[branches['branch_name'] == selected_branch]['branch_id'].values[0]
            branch_sale_ids = sales[sales['branch_id'] == bid]['sale_id']
            payments = payments[payments['sale_id'].isin(branch_sale_ids)]

with col2:
    method_options = ['All'] + list(payments['payment_method'].unique())
    selected_method = st.selectbox("💳 Payment Method", method_options)
    if selected_method != 'All':
        payments = payments[payments['payment_method'] == selected_method]

with col3:
    if not payments.empty:
        payments['payment_date'] = pd.to_datetime(payments['payment_date'])
        min_date = payments['payment_date'].min()
        max_date = payments['payment_date'].max()
        date_range = st.date_input("📅 Date Range", value=(min_date, max_date))
        if len(date_range) == 2:
            payments = payments[
                (payments['payment_date'] >= pd.Timestamp(date_range[0])) &
                (payments['payment_date'] <= pd.Timestamp(date_range[1]))
            ]

st.markdown("---")

# ── SUMMARY METRICS ───────────────────────────────────────────────────────────
st.subheader("📊 Payment Summary")
col1, col2, col3, col4 = st.columns(4)
total_paid = payments['amount_paid'].sum()
cash_total = payments[payments['payment_method'] == 'Cash']['amount_paid'].sum()
card_total = payments[payments['payment_method'] == 'Card']['amount_paid'].sum()
upi_total  = payments[payments['payment_method'] == 'UPI']['amount_paid'].sum()

with col1:
    st.metric("💰 Total Payments", f"₹{total_paid:,.2f}")
with col2:
    st.metric("💵 Cash", f"₹{cash_total:,.2f}")
with col3:
    st.metric("💳 Card", f"₹{card_total:,.2f}")
with col4:
    st.metric("📲 UPI", f"₹{upi_total:,.2f}")

st.markdown("---")

# ── PAYMENT RECORDS TABLE ─────────────────────────────────────────────────────
st.subheader("📋 Payment Records")

if payments.empty:
    st.info("No payment records found.")
else:
    header_cols = st.columns([1, 2, 2, 2, 2, 1, 1])
    for col, h in zip(header_cols, ["Pay ID", "Sale ID", "Date", "Amount", "Method", "✏️", "🗑️"]):
        col.markdown(f"**{h}**")

    for _, row in payments.iterrows():
        pid  = row['payment_id']
        cols = st.columns([1, 2, 2, 2, 2, 1, 1])
        cols[0].write(pid)
        cols[1].write(row['sale_id'])
        cols[2].write(str(row['payment_date'])[:10])
        cols[3].write(f"₹{row['amount_paid']:,.2f}")
        cols[4].write(row['payment_method'])

        if cols[5].button("✏️", key=f"ep_{pid}"):
            st.session_state['edit_payment_id'] = pid
            st.session_state['delete_confirm_payment_id'] = None

        if cols[6].button("🗑️", key=f"dp_{pid}"):
            st.session_state['delete_confirm_payment_id'] = pid
            st.session_state['edit_payment_id'] = None

st.write(f"Total Records: {len(payments)}")

# ── DELETE CONFIRMATION ───────────────────────────────────────────────────────
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
        st.rerun()

# ── EDIT FORM ─────────────────────────────────────────────────────────────────
if st.session_state['edit_payment_id']:
    edit_id  = st.session_state['edit_payment_id']
    # Reload unfiltered payments so the row is always findable
    all_payments = get_payment_splits()
    pay_row  = all_payments[all_payments['payment_id'] == edit_id]

    if pay_row.empty:
        st.warning("Payment not found.")
    else:
        p = pay_row.iloc[0]
        st.markdown("---")
        st.subheader(f"✏️ Edit Payment ID: {edit_id}")

        # Pending amount for the linked sale (excluding this payment)
        linked_sale  = sales[sales['sale_id'] == p['sale_id']]
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
            cancel = c2.form_submit_button("❌ Cancel", use_container_width=True)

        if save:
            if edit_amount <= 0:
                st.error("Amount must be greater than 0!")
            elif not linked_sale.empty and edit_amount > current_pending:
                st.error(f"Amount exceeds pending balance of ₹{current_pending:,.2f}!")
            else:
                update_payment(edit_id, edit_date, edit_amount, edit_method)
                st.session_state['edit_payment_id'] = None
                st.success("✅ Payment updated successfully!")
                st.rerun()
        if cancel:
            st.session_state['edit_payment_id'] = None
            st.rerun()

st.markdown("---")

# ── ADD NEW PAYMENT ───────────────────────────────────────────────────────────
st.subheader("➕ Add New Payment")

# Build a friendly label for each sale
sales['label'] = sales['sale_id'].astype(str)
   
open_sales = sales[sales['status'].str.capitalize() == 'Open']

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

        if submit:
            if amount_paid <= 0:
                st.error("Please enter a valid amount!")
            elif amount_paid > pending:
                st.error(f"Amount exceeds pending balance of ₹{pending:,.2f}!")
            else:
                add_payment(selected_sale_id, payment_date, amount_paid, payment_method)
                st.success("✅ Payment added successfully!")
                st.rerun()

if st.button("View Payment Reports", type='primary'):
    st.switch_page("pages/4_Reports.py")
    