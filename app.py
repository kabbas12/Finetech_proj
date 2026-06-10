import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# CSV file paths
EXPENSES_FILE = 'expenses.csv'

# Load expenses data
def load_expenses():
    if os.path.exists(EXPENSES_FILE):
        return pd.read_csv(EXPENSES_FILE)
    else:
        return pd.DataFrame(columns=['date', 'category', 'amount', 'description'])

# Save expenses data
def save_expenses(df):
    df.to_csv(EXPENSES_FILE, index=False)

# Initialize data
if 'expenses' not in st.session_state:
    st.session_state.expenses = load_expenses()

# Page config
st.set_page_config(page_title="Financial Advisor", page_icon="💰", layout="wide")

st.title("💰 Simple Financial Advisor")
st.markdown("---")

# Sidebar menu
menu = st.sidebar.radio("Menu", ["Dashboard", "Add Expense", "Investment Advice"])

# ==================== DASHBOARD ====================
if menu == "Dashboard":
    st.header("📊 Your Spending Dashboard")
    
    if len(st.session_state.expenses) > 0:
        # Convert date column
        st.session_state.expenses['date'] = pd.to_datetime(st.session_state.expenses['date'])
        
        # Current month expenses
        current_month = datetime.now().strftime('%Y-%m')
        monthly_data = st.session_state.expenses[
            st.session_state.expenses['date'].dt.strftime('%Y-%m') == current_month
        ]
        
        if len(monthly_data) > 0:
            # Show metrics
            total = monthly_data['amount'].sum()
            avg = monthly_data['amount'].mean()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Expenses This Month", f"${total:,.2f}")
            col2.metric("Average Expense", f"${avg:,.2f}")
            col3.metric("Number of Expenses", len(monthly_data))
            
            # Spending by category chart
            st.subheader("Spending by Category")
            category_totals = monthly_data.groupby('category')['amount'].sum()
            
            fig = px.pie(
                values=category_totals.values,
                names=category_totals.index,
                title="Where your money goes"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show recent expenses
            st.subheader("Recent Expenses")
            st.dataframe(
                monthly_data[['date', 'category', 'amount', 'description']].sort_values('date', ascending=False),
                use_container_width=True
            )
        else:
            st.info("No expenses recorded this month. Add some expenses to see insights!")
    else:
        st.info("No data yet. Go to 'Add Expense' to get started!")

# ==================== ADD EXPENSE ====================
elif menu == "Add Expense":
    st.header("➕ Add New Expense")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now())
            category = st.selectbox(
                "Category",
                ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]
            )
        
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.01, step=10.0)
            description = st.text_input("Description", placeholder="What did you spend on?")
        
        submitted = st.form_submit_button("Save Expense", use_container_width=True)
        
        if submitted:
            new_expense = pd.DataFrame({
                'date': [date],
                'category': [category],
                'amount': [amount],
                'description': [description]
            })
            
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
            save_expenses(st.session_state.expenses)
            st.success(f"✅ Saved ${amount:,.2f} for {category}!")
            st.balloons()

# ==================== INVESTMENT ADVICE ====================
elif menu == "Investment Advice":
    st.header("📈 Investment Suggestions")
    
    st.markdown("""
    Based on your monthly savings, here are investment recommendations.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_income = st.number_input("Monthly Income ($)", min_value=0, value=3000, step=500)
        monthly_expenses = st.number_input("Monthly Expenses ($)", min_value=0, value=2000, step=100)
    
    with col2:
        risk_level = st.select_slider(
            "Risk Tolerance",
            options=["Low", "Medium", "High"],
            value="Medium"
        )
        time_horizon = st.selectbox(
            "Investment Time Horizon",
            ["Short-term (1-3 years)", "Medium-term (3-7 years)", "Long-term (7+ years)"]
        )
    
    if monthly_income > monthly_expenses:
        savings = monthly_income - monthly_expenses
        st.success(f"💰 You can save **${savings:,.2f}** per month!")
        
        # Investment suggestions based on risk
        st.subheader("💡 Recommended Investment Options")
        
        if risk_level == "Low":
            st.info("""
            **Conservative Portfolio (Low Risk)**
            - 📊 **Allocation:** 50% Bonds, 30% Fixed Deposits, 20% Blue-chip Stocks
            - 📈 **Expected Return:** 6-8% per year
            - ⏱️ **Suggested Duration:** 1-3 years
            - 💵 **Monthly Investment:** ${:,.2f}
            
            **Why this works for you:** Low-risk investments protect your capital while providing steady growth.
            """.format(savings * 0.7))
            
        elif risk_level == "Medium":
            st.info("""
            **Moderate Portfolio (Medium Risk)**
            - 📊 **Allocation:** 40% Index Funds, 30% Corporate Bonds, 30% Growth Stocks
            - 📈 **Expected Return:** 10-12% per year
            - ⏱️ **Suggested Duration:** 3-7 years
            - 💵 **Monthly Investment:** ${:,.2f}
            
            **Why this works for you:** Balanced approach offers good growth with moderate volatility.
            """.format(savings * 0.7))
            
        else:  # High risk
            st.info("""
            **Aggressive Portfolio (High Risk)**
            - 📊 **Allocation:** 50% Growth Stocks, 30% Tech Stocks, 20% Emerging Markets
            - 📈 **Expected Return:** 15-20% per year
            - ⏱️ **Suggested Duration:** 5+ years
            - 💵 **Monthly Investment:** ${:,.2f}
            
            **Why this works for you:** Higher risk tolerance allows for potentially higher returns over time.
            """.format(savings * 0.7))
        
        # Calculate future value
        st.subheader("📊 Potential Growth Projection")
        
        if risk_level == "Low":
            annual_return = 7
        elif risk_level == "Medium":
            annual_return = 11
        else:
            annual_return = 17
        
        monthly_investment = savings * 0.7
        monthly_rate = annual_return / 100 / 12

        # check
        projection_years = st.slider("Project for (years)", 1, 20, 5)
        months = projection_years * 12
        
        future_value = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        
        col1, col2 = st.columns(2)
        col1.metric("Monthly Investment", f"${monthly_investment:,.2f}")
        col2.metric(f"Value after {projection_years} years", f"${future_value:,.2f}")
        
        st.caption(f"*Assuming {annual_return}% average annual return, compounding monthly*")
        
    else:
        st.error(f"⚠️ You're spending more than you earn! Deficit: ${monthly_expenses - monthly_income:,.2f}")
        st.markdown("""
        **Tips to balance your budget:**
        - Track all your expenses (use the 'Add Expense' tab)
        - Cut unnecessary subscriptions
        - Cook at home more often
        - Use public transportation
        """)

# Footer
st.markdown("---")
st.caption("⚠️ This is for educational purposes only. Consult a financial advisor for real investment decisions.")
