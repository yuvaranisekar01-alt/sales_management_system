import streamlit as st
from Database import get_connection, create_tables
from Database import check_login

#login page
st.set_page_config(layout="centered", page_title="Sales Management System", page_icon=":bar_chart:")


st.title('📊Sales Management System' , text_alignment= 'center')
st.image('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSEwMyocbyeZg3Pu4Vkv3QwX8nC6jfrgHPupA&s', width= 200) 

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
.stApp {
   # background-color: ##eaf3ff;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style = text-align: center; >🔐 Login Page</h2>", unsafe_allow_html=True)
username = st.text_input("👤 Username", placeholder="Enter your username")
password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")

login_button = st.button('LOGIN',  type = 'primary')

if login_button:
    if username == "" or password == "":
        st.error("Please enter both username and password")
    else:
        user = check_login(username, password)
        if user is None:
            st.error("Invalid username or password")
        else:
            st.session_state['username'] = user[1]
            st.session_state['role'] = user[4]
            st.session_state['branch_id'] = user[3]
            st.success("Welcome, " + user[1] + "!")
            st.switch_page("pages/1_Dashboard.py")

            