"""SmartBudget AI — Streamlit frontend.

Run the backend first (uvicorn main:app --reload), then:
    streamlit run frontend/app.py
"""
import os

import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_V1 = f"{API_BASE}/api/v1"

st.set_page_config(page_title="SmartBudget AI", page_icon="💰", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_get(path):
    try:
        r = requests.get(f"{API_V1}{path}", headers=auth_headers(), timeout=10)
        if r.status_code == 200:
            return r.json(), None
        if r.status_code == 401:
            st.session_state.token = None
            st.session_state.user_id = None
            return None, "Session expired. Please log in again."
        return None, r.json().get("detail", f"Error {r.status_code}")
    except requests.exceptions.ConnectionError:
        return None, "Can't reach the backend. Is `uvicorn main:app --reload` running?"


def api_post(path, payload, authed=True):
    try:
        headers = auth_headers() if authed else {}
        r = requests.post(f"{API_V1}{path}", json=payload, headers=headers, timeout=15)
        if r.status_code in (200, 201):
            return r.json(), None
        if r.status_code == 401:
            st.session_state.token = None
            st.session_state.user_id = None
            return None, "Session expired. Please log in again."
        return None, r.json().get("detail", f"Error {r.status_code}")
    except requests.exceptions.ConnectionError:
        return None, "Can't reach the backend. Is `uvicorn main:app --reload` running?"


# ================= LOGIN / REGISTER GATE =================
if not st.session_state.token:
    st.title("💰 SmartBudget AI")
    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")
        if submitted:
            result, error = api_post("/auth/login", {"email": email, "password": password}, authed=False)
            if error:
                st.error(error)
            else:
                st.session_state.token = result["access_token"]
                st.session_state.user_id = result["user_id"]
                st.rerun()

    with tab_register:
        with st.form("register_form"):
            new_user_id = st.text_input("Choose a User ID", placeholder="e.g. sri001")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password (min 8 characters)", type="password")
            submitted = st.form_submit_button("Create Account")
        if submitted:
            result, error = api_post("/auth/register", {
                "user_id": new_user_id, "email": new_email, "password": new_password,
            }, authed=False)
            if error:
                st.error(error)
            else:
                st.session_state.token = result["access_token"]
                st.session_state.user_id = result["user_id"]
                st.success("Account created!")
                st.rerun()

    st.stop()

# ================= AUTHENTICATED APP =================
st.sidebar.title("💰 SmartBudget AI")
st.sidebar.write(f"Logged in as **{st.session_state.user_id}**")
if st.sidebar.button("Log Out"):
    st.session_state.token = None
    st.session_state.user_id = None
    st.rerun()

page = st.sidebar.radio(
    "Navigate",
    ["Profile Setup", "Log Expense", "Budget", "Health Score", "Full Report"],
)

# ================= PROFILE SETUP =================
if page == "Profile Setup":
    st.header("Set Up Your Financial Profile")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            income = st.number_input("Monthly income (₹)", min_value=0.0, value=60000.0, step=1000.0)
            risk = st.selectbox("Risk tolerance", ["low", "moderate", "high"], index=1)
            savings_goal = st.number_input("Monthly savings goal (₹)", min_value=0.0, value=8000.0, step=500.0)
        with col2:
            ef_target = st.number_input("Emergency fund target (₹)", min_value=0.0, value=180000.0, step=5000.0)
            ef_current = st.number_input("Emergency fund current (₹)", min_value=0.0, value=30000.0, step=1000.0)

        st.subheader("Debts (optional)")
        num_debts = st.number_input("Number of debts", min_value=0, max_value=10, value=1, step=1)
        debts = []
        for i in range(int(num_debts)):
            st.markdown(f"**Debt {i+1}**")
            dcol1, dcol2, dcol3, dcol4 = st.columns(4)
            name = dcol1.text_input(f"Name##{i}", value="Education Loan" if i == 0 else "")
            balance = dcol2.number_input(f"Balance##{i}", min_value=0.0, value=200000.0 if i == 0 else 0.0)
            rate = dcol3.number_input(f"Interest %##{i}", min_value=0.0, value=9.5 if i == 0 else 0.0)
            min_pay = dcol4.number_input(f"Min payment##{i}", min_value=0.0, value=4000.0 if i == 0 else 0.0)
            if name:
                debts.append({"name": name, "balance": balance, "interest_rate": rate, "min_payment": min_pay})

        submitted = st.form_submit_button("Save Profile")

    if submitted:
        payload = {
            "monthly_income": income,
            "risk_tolerance": risk,
            "savings_goal": savings_goal,
            "emergency_fund_target": ef_target,
            "emergency_fund_current": ef_current,
            "debts": debts,
        }
        result, error = api_post("/profile", payload)
        if error:
            st.error(error)
        else:
            st.success("Profile saved. A budget has been generated — check the Budget tab.")

# ================= LOG EXPENSE =================
elif page == "Log Expense":
    st.header("Log an Expense")

    text = st.text_input("Describe the expense", placeholder="e.g. spent 500 on groceries today")
    if st.button("Log Expense") and text:
        result, error = api_post("/expense", {"text": text})
        if error:
            st.error(error)
        else:
            st.success(result["message"])
            c1, c2 = st.columns(2)
            c1.metric("Category", result["category"])
            c2.metric("Amount", f"₹{result['amount']:,.0f}")

# ================= BUDGET =================
elif page == "Budget":
    st.header("Monthly Budget")

    data, error = api_get("/budget")
    if error:
        st.error(error)
    else:
        st.caption(data["reasoning"])
        st.metric("Total Income", f"₹{data['total_income']:,.0f}")

        df = pd.DataFrame(data["categories"])
        df_display = df.rename(columns={
            "category": "Category", "allocated": "Allocated (₹)",
            "spent": "Spent (₹)", "remaining": "Remaining (₹)",
            "percent_of_income": "% of Income",
        })
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        chart_df = df.set_index("category")[["allocated", "spent"]]
        st.bar_chart(chart_df)

# ================= HEALTH SCORE =================
elif page == "Health Score":
    st.header("Financial Health Score")

    data, error = api_get("/health-score")
    if error:
        st.error(error)
    else:
        score = data["score"]
        st.metric("Overall Score", f"{score}/100")
        st.progress(score / 100)
        st.write(data["summary"])

        st.subheader("Breakdown")
        breakdown_df = pd.DataFrame(
            [{"Component": k.replace("_", " ").title(), "Points": v} for k, v in data["breakdown"].items()]
        )
        st.bar_chart(breakdown_df.set_index("Component"))

# ================= FULL REPORT =================
elif page == "Full Report":
    st.header("Monthly Report")

    data, error = api_get("/report")
    if error:
        st.error(error)
    else:
        st.subheader(f"Report for {data['month']}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Health Score", f"{data['health_score']['score']}/100")
        col2.metric("Total Income", f"₹{data['budget']['total_income']:,.0f}")
        col3.metric("Emergency Fund", f"{data['savings_progress']['percent_complete']}%")

        st.subheader("Key Insights")
        for insight in data["insights"]:
            st.write(f"• {insight}")

        st.subheader("Action Items")
        for action in data["action_items"]:
            st.checkbox(action, key=action)

        st.subheader("Debt Plan")
        if data["debt_plan"]["order"]:
            st.write(data["debt_plan"]["note"])
            debt_df = pd.DataFrame(data["debt_plan"]["order"])
            st.dataframe(debt_df, use_container_width=True, hide_index=True)
        else:
            st.write("No debts on file.")

        with st.expander("Full Budget Breakdown"):
            budget_df = pd.DataFrame(data["budget"]["categories"])
            st.dataframe(budget_df, use_container_width=True, hide_index=True)
