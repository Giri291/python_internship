# giri.py
import streamlit as st
from utils import (
    create_tables,
    signup,
    login,
    deposit,
    withdraw,
    transfer,
    get_balance,
    get_transactions,
    get_all_users,
)

# Initialize DB & tables
create_tables()

# Page config
st.set_page_config(page_title="Bank Management System", page_icon="🏦", layout="wide")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def do_logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out successfully.")
    


# Title
st.title("🏦 Bank Management System Using Python")

# Sidebar navigation
if st.session_state.logged_in:
    choice = st.sidebar.selectbox("Menu", ["Dashboard", "Admin Panel", "Logout"])
else:
    choice = st.sidebar.selectbox("Menu", ["Signup", "Login"])

# Handle Logout from sidebar
if choice == "Logout":
    do_logout()

# Signup page
if choice == "Signup":
    st.subheader("Create New Account")
    with st.form("signup_form"):
        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Signup")
        if submitted:
            if not uname or not pwd:
                st.warning("Please enter both username and password.")
            else:
                if signup(uname.strip(), pwd):
                    st.success("Account created successfully. Please login.")
                else:
                    st.error("Username already exists or signup failed.")

# Login page
elif choice == "Login":
    st.subheader("Login to Your Account")
    with st.form("login_form"):
        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if login(uname.strip(), pwd):
                st.session_state.logged_in = True
                st.session_state.username = uname.strip()
                st.success("Logged in successfully.")
            else:
                st.error("Invalid username or password.")

# Dashboard for logged-in users
elif choice == "Dashboard" and st.session_state.logged_in:
    st.subheader(f"Welcome, {st.session_state.username} 👋")
    balance = get_balance(st.session_state.username)
    st.info(f"💰 Current Balance: ₹{balance:,.2f}")

    action = st.radio("Choose Action", ["Deposit", "Withdraw", "Transfer", "Transaction History"], horizontal=True)

    if action == "Deposit":
        st.subheader("Deposit Funds")
        with st.form("deposit_form"):
            amt = st.number_input("Amount to deposit (₹)", min_value=0.01, format="%.2f")
            submitted = st.form_submit_button("Deposit")
            if submitted:
                if deposit(st.session_state.username, float(amt)):
                    st.success(f"Deposited ₹{amt:,.2f} successfully.")
                else:
                    st.error("Deposit failed. Enter a valid amount.")

    elif action == "Withdraw":
        st.subheader("Withdraw Funds")
        with st.form("withdraw_form"):
            amt = st.number_input("Amount to withdraw (₹)", min_value=0.01, format="%.2f")
            submitted = st.form_submit_button("Withdraw")
            if submitted:
                if withdraw(st.session_state.username, float(amt)):
                    st.success(f"Withdrawn ₹{amt:,.2f} successfully.")
                else:
                    st.error("Withdrawal failed. Check your balance or enter a valid amount.")

    elif action == "Transfer":
        st.subheader("Transfer Funds")
        with st.form("transfer_form"):
            receiver = st.text_input("Receiver Username")
            amt = st.number_input("Amount to transfer (₹)", min_value=0.01, format="%.2f")
            submitted = st.form_submit_button("Transfer")
            if submitted:
                if receiver.strip() == st.session_state.username:
                    st.error("Cannot transfer to the same account.")
                else:
                    ok = transfer(st.session_state.username, receiver.strip(), float(amt))
                    if ok:
                        st.success(f"Transferred ₹{amt:,.2f} to {receiver.strip()} successfully.")
                    else:
                        st.error("Transfer failed. Check receiver username and your balance.")

    elif action == "Transaction History":
        st.subheader("Your Transaction History")
        txns = get_transactions(st.session_state.username)
        if not txns:
            st.info("No transactions found.")
        else:
            # Show most recent first
            for t in reversed(txns):
                t_type, t_amt, t_time, t_other = t
                col1, col2 = st.columns([3, 7])
                with col1:
                    if t_type.lower() in ("deposit", "transfer_in"):
                        st.markdown(f"**{t_type.capitalize()}** — +₹{t_amt:,.2f}")
                    else:
                        st.markdown(f"**{t_type.capitalize()}** — -₹{t_amt:,.2f}")
                with col2:
                    details = t_time
                    if t_other:
                        if t_type == "transfer_out":
                            details = f"To: {t_other} | {t_time}"
                        elif t_type == "transfer_in":
                            details = f"From: {t_other} | {t_time}"
                    st.write(details)
            st.write("---")

# Admin Panel (simple, accessible to any logged-in user for demo)
elif choice == "Admin Panel" and st.session_state.logged_in:
    st.subheader("Admin Panel — All Users")
    st.warning("This admin view is for demonstration and is accessible to any logged-in user.")
    users = get_all_users()
    if not users:
        st.info("No users available.")
    else:
        for u in users:
            st.write(f"**Username:** {u[0]} — Balance: ₹{u[1]:,.2f}")

# Access control warning
if choice in ["Dashboard", "Admin Panel"] and not st.session_state.logged_in:
    st.warning("Please login to access this page.")
