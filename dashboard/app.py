import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

import os
API_URL = os.getenv("API_URL", "http://localhost:5000/api")

# For the Render environment, the API_URL will be read from the environment variable.
# For local development, it will fall back to http://localhost:5000/api.

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'businesses' not in st.session_state:
    st.session_state.businesses = []
if 'selected_business' not in st.session_state:
    st.session_state.selected_business = None
if 'requests_session' not in st.session_state:
    st.session_state.requests_session = requests.Session()
if 'signup_success' not in st.session_state:
    st.session_state.signup_success = False
if 'add_biz_counter' not in st.session_state:
    st.session_state.add_biz_counter = 0
if 'show_add_business' not in st.session_state:
    st.session_state.show_add_business = False

st.set_page_config(page_title="M-Pesa Monitor", page_icon="💳", layout="wide")


def api_request(method, endpoint, **kwargs):
    """Persistent session with cookie handling."""
    url = f"{API_URL}{endpoint}"
    try:
        session = st.session_state.requests_session
        if method == "GET":
            response = session.get(url, **kwargs)
        elif method == "POST":
            response = session.post(url, json=kwargs.get('json'))
        else:
            return None
        return response
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 💳 M-Pesa Monitor")
        st.markdown("### Track payments in real-time")
        st.markdown("---")

        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    response = api_request("POST", "/login", json={"email": email, "password": password})
                    if response and response.status_code == 200:
                        data = response.json()
                        st.session_state.authenticated = True
                        st.session_state.user = data['user']
                        st.rerun()
                    elif response:
                        st.error(response.json().get('error', 'Login failed'))

        with tab2:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if password != confirm:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        response = api_request("POST", "/signup", json={
                            "email": email, "password": password, "full_name": full_name
                        })
                        if response and response.status_code == 201:
                            st.session_state.signup_success = True
                            st.rerun()
                        elif response:
                            st.error(response.json().get('error', 'Signup failed'))

    if st.session_state.signup_success:
        st.session_state.signup_success = False
        st.success("✅ Account created! Please login.")


def onboarding_page():
    # Cancel button to go back to dashboard
    if st.session_state.get('show_add_business') and st.session_state.businesses:
        if st.button("← Back to Dashboard"):
            st.session_state.show_add_business = False
            st.rerun()

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(f"## 👋 Welcome, {st.session_state.user.get('full_name', 'User')}!")
        st.markdown("### Add Your First Business" if not st.session_state.businesses else "### Add Another Business")

        # Dynamic form key ensures a fresh form every time
        form_key = f"add_business_form_{st.session_state.add_biz_counter}"
        with st.form(key=form_key):
            business_name = st.text_input("Business Name", placeholder="e.g., My Supermarket")
            col_a, col_b = st.columns(2)
            with col_a:
                shortcode_type = st.selectbox("Type", ["till", "paybill"])
            with col_b:
                shortcode = st.text_input("Number", placeholder="e.g., 123456")
            st.info("""
            After adding your business, register your webhook URL with Safaricom Daraja.
            **Confirmation URL:** `https://your-domain.com/confirmation`
            """)
            if st.form_submit_button("➕ Add Business", use_container_width=True):
                if not business_name or not shortcode:
                    st.error("Please fill all fields")
                else:
                    response = api_request("POST", "/businesses", json={
                        "business_name": business_name,
                        "shortcode": shortcode,
                        "shortcode_type": shortcode_type
                    })
                    if response:
                        if response.status_code == 201:
                            st.success("✅ Business added!")
                            st.session_state.add_biz_counter += 1
                            st.session_state.show_add_business = False
                            st.rerun()
                        else:
                            st.error(response.json().get('error', 'Failed to add business'))
                    else:
                        st.error("No response from server.")


def main_dashboard():
    with st.sidebar:
        st.markdown("## 💳 M-Pesa Monitor")
        st.markdown(f"**{st.session_state.user.get('full_name', 'User')}**")
        st.caption(st.session_state.user.get('email', ''))
        st.divider()

        response = api_request("GET", "/businesses")
        if response and response.status_code == 200:
            st.session_state.businesses = response.json()

        if st.session_state.businesses:
            business_options = {b['business_name']: b['id'] for b in st.session_state.businesses}
            selected_name = st.selectbox("📋 Select Business", options=list(business_options.keys()))
            st.session_state.selected_business = business_options[selected_name]
        else:
            st.warning("No businesses yet")
            st.session_state.selected_business = None

        st.divider()
        if st.button("➕ Add Business", use_container_width=True):
            st.session_state.show_add_business = True
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            api_request("POST", "/logout")
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

    # Decide which page to show
    if st.session_state.get('show_add_business') or not st.session_state.businesses:
        onboarding_page()
    elif st.session_state.selected_business:
        business_name = next(
            (b['business_name'] for b in st.session_state.businesses if b['id'] == st.session_state.selected_business),
            "Business"
        )
        st.markdown(f"## 📊 {business_name}")

        col1, col2 = st.columns([3, 1])
        with col1:
            search_phone = st.text_input("🔍 Search by Phone Number", placeholder="e.g., 0712345678")
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        params = {"business_id": st.session_state.selected_business}
        if search_phone:
            params["search"] = search_phone

        response = api_request("GET", "/payments", params=params)
        if response and response.status_code == 200:
            payments = response.json()
            if payments:
                df = pd.DataFrame(payments)
                df['transaction_time'] = pd.to_datetime(df['transaction_time'])
                df['amount'] = df['amount'].astype(float)
                df['date'] = df['transaction_time'].dt.date

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Transactions", len(df))
                with col2:
                    st.metric("Total Revenue", f"KES {df['amount'].sum():,.2f}")
                with col3:
                    today = datetime.now().date()
                    today_df = df[df['date'] == today]
                    st.metric("Today's Revenue", f"KES {today_df['amount'].sum():,.2f}")
                with col4:
                    avg = df['amount'].mean() if len(df) > 0 else 0
                    st.metric("Average", f"KES {avg:,.2f}")

                st.divider()
                tab1, tab2 = st.tabs(["📈 Charts", "📋 Transactions"])

                with tab1:
                    daily = df.groupby('date')['amount'].sum().reset_index().sort_values('date', ascending=False).head(14)
                    fig = px.bar(daily, x='date', y='amount', title="Daily Revenue (Last 14 days)",
                                 labels={'date': 'Date', 'amount': 'Amount (KES)'}, color_discrete_sequence=['#1DB954'])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    display_df = df.copy()
                    display_df['Time'] = display_df['transaction_time'].dt.strftime('%Y-%m-%d %H:%M')
                    display_df['Amount'] = display_df['amount'].apply(lambda x: f"KES {x:,.2f}")
                    st.dataframe(
                        display_df[['Time', 'phone_masked', 'Amount', 'mpesa_code']],
                        use_container_width=True, hide_index=True,
                        column_config={"Time": "Date & Time", "phone_masked": "Phone", "Amount": "Amount", "mpesa_code": "M-Pesa Code"}
                    )
                    csv = display_df.to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, f"transactions_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            else:
                st.info("📭 No transactions yet.")
        else:
            st.error("⚠️ Unable to load data.")


def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()