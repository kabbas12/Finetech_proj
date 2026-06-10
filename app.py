import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os
import json
from openai import OpenAI

# Initialize OpenAI client (you'll need to add your API key to secrets)
# For demo, we'll use mock responses if no API key is provided

# File paths
EXPENSES_FILE = 'expenses.csv'
INVESTMENTS_FILE = 'investments.csv'
BUDGET_FILE = 'budget.csv'

# Initialize session state
if 'expenses' not in st.session_state:
    if os.path.exists(EXPENSES_FILE):
        st.session_state.expenses = pd.read_csv(EXPENSES_FILE)
    else:
        st.session_state.expenses = pd.DataFrame(columns=['date', 'category', 'amount', 'description'])

if 'investments' not in st.session_state:
    if os.path.exists(INVESTMENTS_FILE):
        st.session_state.investments = pd.read_csv(INVESTMENTS_FILE)
    else:
        st.session_state.investments = pd.DataFrame(columns=['date', 'type', 'amount', 'expected_return', 'duration_years'])

if 'budget' not in st.session_state:
    if os.path.exists(BUDGET_FILE):
        st.session_state.budget = pd.read_csv(BUDGET_FILE)
    else:
        st.session_state.budget = pd.DataFrame(columns=['month', 'income', 'savings_goal', 'investment_goal'])

# Helper functions
def save_expenses():
    st.session_state.expenses.to_csv(EXPENSES_FILE, index=False)

def save_investments():
    st.session_state.investments.to_csv(INVESTMENTS_FILE, index=False)

def save_budget():
    st.session_state.budget.to_csv(BUDGET_FILE, index=False)

def analyze_spending_patterns():
    if len(st.session_state.expenses) == 0:
        return None
    
    df = st.session_state.expenses
    df['date'] = pd.to_datetime(df['date'])
    
    # Get current month expenses
    current_month = datetime.now().strftime('%Y-%m')
    monthly_expenses = df[df['date'].dt.strftime('%Y-%m') == current_month]
    
    if len(monthly_expenses) > 0:
        spending_by_category = monthly_expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
        total_monthly = monthly_expenses['amount'].sum()
        avg_daily = monthly_expenses.groupby(df['date'].dt.date)['amount'].sum().mean()
        
        return {
            'total': total_monthly,
            'by_category': spending_by_category,
            'avg_daily': avg_daily,
            'top_category': spending_by_category.index[0] if len(spending_by_category) > 0 else None
        }
    return None

def suggest_investments(monthly_savings, risk_tolerance):
    """
    Suggest investments based on savings amount and risk tolerance
    """
    suggestions = []
    
    # Conservative portfolio (low risk)
    conservative = {
        'type': 'Conservative Portfolio',
        'allocation': {
            'Treasury Bonds (5-7% annual)': 50,
            'Fixed Deposits (6-8% annual)': 30,
            'Blue-chip Stocks (8-10% annual)': 20
        },
        'expected_return': 6.5,
        'min_duration': 1,
        'max_duration': 3,
        'risk_level': 'Low'
    }
    
    # Moderate portfolio (medium risk)
    moderate = {
        'type': 'Moderate Portfolio',
        'allocation': {
            'Index Funds (10-12% annual)': 40,
            'Corporate Bonds (7-9% annual)': 30,
            'Growth Stocks (12-15% annual)': 30
        },
        'expected_return': 10.5,
        'min_duration': 3,
        'max_duration': 7,
        'risk_level': 'Medium'
    }
    
    # Aggressive portfolio (high risk)
    aggressive = {
        'type': 'Aggressive Portfolio',
        'allocation': {
            'Tech Stocks (15-20% annual)': 40,
            'Cryptocurrency (20-40% annual)': 20,
            'Emerging Markets (12-18% annual)': 40
        },
        'expected_return': 18.0,
        'min_duration': 5,
        'max_duration': 10,
        'risk_level': 'High'
    }
    
    if risk_tolerance == 'Low':
        primary = conservative
        secondary = moderate
    elif risk_tolerance == 'High':
        primary = aggressive
        secondary = moderate
    else:  # Medium
        primary = moderate
        secondary = conservative
    
    # Calculate recommended investment amount
    recommended_amount = monthly_savings * 0.7  # Invest 70% of savings
    
    # Calculate projections
    projection_years = primary['min_duration']
    future_value = recommended_amount * 12 * ((1 + primary['expected_return']/100) ** projection_years - 1) / (primary['expected_return']/100) * (1 + primary['expected_return']/100)
    
    suggestions.append({
        'primary': primary,
        'secondary': secondary,
        'recommended_monthly': recommended_amount,
        'projected_value': future_value,
        'projection_years': projection_years
    })
    
    return suggestions

def get_ai_advice(user_query, financial_data):
    """
    Generate AI advice using OpenAI or provide mock advice if no API key
    """
    # Check for OpenAI API key in secrets
    try:
        client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
        
        prompt = f"""
        As a financial advisor AI, please answer this question: {user_query}
        
        Financial context:
        - Monthly expenses: {financial_data.get('monthly_expenses', 'N/A')}
        - Savings capacity: {financial_data.get('savings', 'N/A')}
        - Current investments: {financial_data.get('investments', 'N/A')}
        
        Provide practical, actionable advice considering risk management and long-term wealth building.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional financial advisor providing practical investment advice."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        # Mock AI responses when no API key is available
        mock_responses = {
            "save more": "Based on your spending patterns, I recommend following the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings and investments. Try to automate your savings to build wealth consistently.",
            "invest": "For long-term wealth building, consider a diversified portfolio of low-cost index funds. Historically, the S&P 500 returns about 10% annually. Start with a robo-advisor if you're new to investing.",
            "retirement": "Aim to save 15% of your pre-tax income for retirement. Consider tax-advantaged accounts and increase your contribution rate by 1% annually until you reach your goal.",
            "default": "To optimize your finances, first build an emergency fund covering 3-6 months of expenses. Then focus on paying high-interest debt before investing. Consider dollar-cost averaging for consistent investment growth."
        }
        
        for key, response in mock_responses.items():
            if key in user_query.lower():
                return response + " (Demo advice - Add OpenAI API key for personalized responses)"
        return mock_responses['default'] + " (Demo advice - Add OpenAI API key for personalized responses)"

# Streamlit UI
st.set_page_config(page_title="AI Financial Advisor", page_icon="💰", layout="wide")

st.title("💰 AI Financial Advisor")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Add Expenses", "Investment Advisor", "Budget Planning", "AI Chat", "View History"])

# Dashboard
if page == "Dashboard":
    st.header("📊 Financial Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    spending_analysis = analyze_spending_patterns()
    
    if spending_analysis:
        col1.metric("💰 Monthly Expenses", f"${spending_analysis['total']:,.2f}")
        col2.metric("📊 Avg Daily Spend", f"${spending_analysis['avg_daily']:,.2f}")
        col3.metric("🎯 Top Category", spending_analysis['top_category'] if spending_analysis['top_category'] else "None")
        
        # Spending by category chart
        if len(spending_analysis['by_category']) > 0:
            st.subheader("Spending by Category")
            fig = px.pie(values=spending_analysis['by_category'].values, 
                        names=spending_analysis['by_category'].index,
                        title="Monthly Expense Distribution")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data available. Please add your expenses to see insights.")

# Add Expenses
elif page == "Add Expenses":
    st.header("➕ Add New Expense")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now())
            category = st.selectbox("Category", 
                                   ["Food", "Transportation", "Rent", "Utilities", 
                                    "Entertainment", "Shopping", "Healthcare", "Other"])
        
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.01, step=10.0)
            description = st.text_input("Description")
        
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            new_expense = pd.DataFrame({
                'date': [date],
                'category': [category],
                'amount': [amount],
                'description': [description]
            })
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
            save_expenses()
            st.success(f"Added ${amount} expense for {category}!")

# Investment Advisor
elif page == "Investment Advisor":
    st.header("📈 Investment Advisor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_income = st.number_input("Monthly Income ($)", min_value=0, step=500)
        monthly_expenses = st.number_input("Monthly Expenses ($)", min_value=0, step=100)
    
    with col2:
        risk_tolerance = st.select_slider("Risk Tolerance", 
                                         options=["Low", "Medium", "High"],
                                         value="Medium")
        investment_goal = st.selectbox("Investment Goal", 
                                      ["Wealth Growth", "Retirement", "Passive Income", "Emergency Fund"])
    
    if monthly_income > monthly_expenses:
        monthly_savings = monthly_income - monthly_expenses
        st.info(f"💰 Your monthly savings potential: **${monthly_savings:,.2f}**")
        
        if st.button("Get Investment Suggestions"):
            suggestions = suggest_investments(monthly_savings, risk_tolerance)
            
            for suggestion in suggestions:
                st.subheader(f"🎯 Recommended: {suggestion['primary']['type']}")
                
                # Display allocation
                st.write("**Portfolio Allocation:**")
                for asset, percentage in suggestion['primary']['allocation'].items():
                    st.write(f"- {asset}: {percentage}%")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Expected Annual Return", f"{suggestion['primary']['expected_return']}%")
                with col2:
                    st.metric("Recommended Duration", f"{suggestion['primary']['min_duration']}-{suggestion['primary']['max_duration']} years")
                with col3:
                    st.metric("Risk Level", suggestion['primary']['risk_level'])
                
                st.write(f"**Recommended Monthly Investment:** ${suggestion['recommended_monthly']:,.2f}")
                st.write(f"**Projected Value after {suggestion['projection_years']} years:** ${suggestion['projected_value']:,.2f}")
                
                # Alternative portfolio
                with st.expander("View Alternative Portfolio"):
                    st.write(f"**Alternative: {suggestion['secondary']['type']}**")
                    st.write(f"Expected Return: {suggestion['secondary']['expected_return']}%")
                    st.write(f"Duration: {suggestion['secondary']['min_duration']}-{suggestion['secondary']['max_duration']} years")
                    st.write(f"Risk: {suggestion['secondary']['risk_level']}")
    else:
        st.error(f"You need to reduce expenses or increase income. Current deficit: ${monthly_expenses - monthly_income:,.2f}")

# Budget Planning
elif page == "Budget Planning":
    st.header("🎯 Budget Planner")
    
    current_month = datetime.now().strftime('%Y-%m')
    
    with st.form("budget_form"):
        income = st.number_input("Monthly Income ($)", min_value=0, step=100)
        savings_goal = st.number_input("Savings Goal ($)", min_value=0, step=50)
        investment_goal = st.number_input("Investment Goal ($)", min_value=0, step=50)
        
        submitted = st.form_submit_button("Save Budget")
        
        if submitted:
            new_budget = pd.DataFrame({
                'month': [current_month],
                'income': [income],
                'savings_goal': [savings_goal],
                'investment_goal': [investment_goal]
            })
            # Remove old budget for same month
            st.session_state.budget = st.session_state.budget[st.session_state.budget['month'] != current_month]
            st.session_state.budget = pd.concat([st.session_state.budget, new_budget], ignore_index=True)
            save_budget()
            st.success("Budget saved!")
    
    # Display budget tips
    if len(st.session_state.budget) > 0:
        st.subheader("💡 Budget Tips")
        
        tips = [
            "📊 Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings",
            "💰 Automate your savings - set up automatic transfers on payday",
            "📉 Track every expense for 30 days to identify spending patterns",
            "🏦 Build an emergency fund covering 3-6 months of expenses",
            "📈 Start investing early to benefit from compound interest"
        ]
        
        for tip in tips:
            st.write(tip)

# AI Chat
elif page == "AI Chat":
    st.header("🤖 AI Financial Assistant")
    
    st.markdown("Ask me anything about personal finance, investments, or money management!")
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI Advisor:** {message['content']}")
        st.markdown("---")
    
    # User input
    user_question = st.text_input("Ask your financial question:")
    
    if st.button("Get Advice") and user_question:
        # Prepare financial context
        spending = analyze_spending_patterns()
        financial_data = {
            'monthly_expenses': spending['total'] if spending else 0,
            'savings': st.session_state.budget['savings_goal'].iloc[-1] if len(st.session_state.budget) > 0 else 0,
            'investments': len(st.session_state.investments)
        }
        
        # Get AI response
        with st.spinner("Getting AI advice..."):
            advice = get_ai_advice(user_question, financial_data)
        
        # Add to history
        st.session_state.chat_history.append({'role': 'user', 'content': user_question})
        st.session_state.chat_history.append({'role': 'assistant', 'content': advice})
        
        st.rerun()

# View History
elif page == "View History":
    st.header("📜 Financial History")
    
    tab1, tab2 = st.tabs(["Expenses", "Investments"])
    
    with tab1:
        if len(st.session_state.expenses) > 0:
            st.dataframe(st.session_state.expenses.sort_values('date', ascending=False))
            
            # Summary statistics
            total_expenses = st.session_state.expenses['amount'].sum()
            avg_expense = st.session_state.expenses['amount'].mean()
            
            col1, col2 = st.columns(2)
            col1.metric("Total Expenses", f"${total_expenses:,.2f}")
            col2.metric("Average Expense", f"${avg_expense:,.2f}")
            
            if st.button("Clear All Expenses"):
                st.session_state.expenses = pd.DataFrame(columns=['date', 'category', 'amount', 'description'])
                save_expenses()
                st.success("All expenses cleared!")
        else:
            st.info("No expenses recorded yet")
    
    with tab2:
        if len(st.session_state.investments) > 0:
            st.dataframe(st.session_state.investments)
            
            total_invested = st.session_state.investments['amount'].sum()
            st.metric("Total Invested", f"${total_invested:,.2f}")
        else:
            st.info("No investments recorded yet")

# Footer
st.markdown("---")
st.markdown("⚠️ **Disclaimer:** This is for educational purposes only. Consult a professional financial advisor before making investment decisions.")
