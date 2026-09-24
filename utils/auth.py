import streamlit as st


# ============================================================
# DEMO USER ACCOUNTS
# ============================================================

DEMO_USERS = {
    "F001": {
        "user_id": "F001",
        "name": "Ramesh Patil",
        "role": "Farmer",
        "icon": "👨‍🌾",
    },
    "F002": {
        "user_id": "F002",
        "name": "Suresh Shinde",
        "role": "Farmer",
        "icon": "👨‍🌾",
    },
    "B001": {
        "user_id": "B001",
        "name": "Pune Fresh Retail",
        "role": "Buyer",
        "icon": "🛒",
    },
    "B002": {
        "user_id": "B002",
        "name": "Green Basket Retail",
        "role": "Buyer",
        "icon": "🛒",
    },
    "C001": {
        "user_id": "C001",
        "name": "Demo Consumer",
        "role": "Consumer",
        "icon": "🛍️",
    },
    "L001": {
        "user_id": "L001",
        "name": "Maharashtra Agro Transport",
        "role": "Logistics",
        "icon": "🚚",
    },
    "ADMIN": {
        "user_id": "ADMIN",
        "name": "Kisan Setu Administrator",
        "role": "Admin",
        "icon": "🏛️",
    },
}


# ============================================================
# SESSION INITIALIZATION
# ============================================================

def initialize_auth():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "user_name" not in st.session_state:
        st.session_state.user_name = None

    if "user_role" not in st.session_state:
        st.session_state.user_role = None


# ============================================================
# LOGIN
# ============================================================

def login(user_id):

    user_id = str(user_id).strip().upper()

    if user_id in DEMO_USERS:

        user = DEMO_USERS[user_id]

        st.session_state.logged_in = True
        st.session_state.user_id = user["user_id"]
        st.session_state.user_name = user["name"]
        st.session_state.user_role = user["role"]

        return True

    return False


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_role = None

    # Clear selected page-related state
    keys_to_clear = [
        "best_buyer",
        "selected_produce_id",
        "selected_order",
    ]

    for key in keys_to_clear:

        if key in st.session_state:
            del st.session_state[key]


# ============================================================
# CURRENT USER
# ============================================================

def current_user():

    return {
        "user_id": st.session_state.get("user_id"),
        "name": st.session_state.get("user_name"),
        "role": st.session_state.get("user_role"),
    }


# ============================================================
# AUTH CHECK
# ============================================================

def is_logged_in():

    return st.session_state.get(
        "logged_in",
        False
    )


# ============================================================
# ROLE CHECK
# ============================================================

def has_role(role):

    return (
        is_logged_in()
        and
        st.session_state.get("user_role")
        == role
    )