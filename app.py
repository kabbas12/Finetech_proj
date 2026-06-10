import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os
import json

# Try to import OpenAI, but don't fail if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.warning("OpenAI package not installed. AI features will use demo mode.")

# File paths
EXPENSES_FILE = 'expenses.csv'
INVESTMENTS_FILE = 'investments.csv'
BUDGET_FILE = 'budget.csv'

# Initialize session state
def init_session_state():
    if 'expenses' not in st.session_state:
        if os.path.exists(EXPENSES_FILE):
            try:
                st.session_state.expenses = pd.read_csv(EXPENSES_FILE)
            except:
                st.session_state.expenses = pd.DataFrame(columns=['date', 'category', 'amount', 'description'])
        else:
            st.session_state.expenses = pd.DataFrame(columns=['date', 'category', 'amount', 'description'])
    
    if 'investments' not in st.session_state:
        if os.path.exists(INVESTMENTS_FILE):
            try:
                st.session_state.investments = pd.read_csv(INVESTMENTS_FILE)
            except:
                st.session_state.investments = pd.DataFrame(columns=['date', 'type', 'amount', 'expected_return', 'duration_years'])
        else:
            st.session_state.investments = pd.DataFrame(columns=['date', 'type', 'amount', 'expected_return', 'duration_years'])
    
    if 'budget' not in st.session_state:
        if os.path.exists(BUDGET_FILE):
            try:
                st.session_state.budget = pd.read_csv(BUDGET_FILE)
            except:
                st.session_state.budget = pd.DataFrame(columns=['month', 'income', 'savings_goal', 'investment_goal'])
        else:
            st.session_state.budget = pd.DataFrame(columns=['month', 'income', 'savings_goal', 'investment_goal'])

# Helper functions
def save_expenses():
    try:
        st.session_state.expenses.to_csv(EXPENSES_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving expenses: {e}")
        return False

def save_investments():
    try:
        st.session_state.investments.to_csv(INVESTMENTS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving investments: {e}")
        return False

def save_budget():
    try:
        st.session_state.budget.to_csv(BUDGET_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving budget: {e}")
        return False

def analyze_spending_patterns():
    if len(st.session_state.expenses) == 0:
        return None
    
    try:
        df = st.session_state.expenses.copy()
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
    except Exception as e:
        st.error(f"Error analyzing spending: {e}")
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
            'Real Estate (10-14% annual)': 30,
            'Emerging Markets (12-18% annual)': 30
        },
        'expected_return': 15.0,
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
    
    # Calculate projections (future value of monthly investments)
    monthly_rate = primary['expected_return'] / 100 / 12
    months = primary['min_duration'] * 12
    if monthly_rate > 0:
        future_value = recommended_amount * ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
    else:
        future_value = recommended_amount * months
    
    suggestions.append({
        'primary': primary,
        'secondary': secondary,
        'recommended_monthly': recommended_amount,
        'projected_value': future_value,
        'projection_years': primary['min_duration']
    })
    
    return suggestions

def get_ai_advice(user_query, financial_data):
    """
    Generate AI advice using OpenAI or provide mock advice if not available
    """
    if OPENAI_AVAILABLE:
        try:
            # Try to get API key from secrets
            api_key = st.secrets.get("OPENAI_API_KEY", "")
            
            if api_key:
                client = OpenAI(api_key=api_key)
                
                prompt = f"""
                As a financial advisor AI, please answer this question: {user_query}
                
                Financial context:
                - Monthly expenses: ${financial_data.get('monthly_expenses', 'N/A')}
                - Savings capacity: ${financial_data.get('savings', 'N/A')}
                - Number of investments: {financial_data.get('investments', 'N/A')}
                
                Provide practical, actionable advice considering risk management and long-term wealth building.
                Keep the response concise and helpful (maximum 200 words).
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional financial advisor providing practical investment advice."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            st.warning(f"OpenAI API error: {e}. Using demo advice.")
    
    # Mock AI responses when no API key is available
    user_query_lower = user_query.lower()
    
    if "save" in user_query_lower or "saving" in user_query_lower:
        return "📊 **Savings Advice:** Based on standard financial principles, I recommend following the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings and investments. Try to automate your savings by setting up automatic transfers on payday. Even saving 10% consistently is better than saving 30% inconsistently."
    
    elif "invest" in user_query_lower or "investment" in user_query_lower:
        return "📈 **Investment Advice:** For long-term wealth building, consider a diversified portfolio of low-cost index funds. Historically, the S&P 500 returns about 10% annually. Start with a robo-advisor if you're new to investing. Remember: Time in the market beats timing the market."
    
    elif "retirement" in user_query_lower:
        return "🏦 **Retirement Planning:** Aim to save 15% of your pre-tax income for retirement. Consider tax-advantaged accounts and increase your contribution rate by 1% annually until you reach your goal. The power of compound interest means starting early is more important than investing large amounts later."
    
    elif "debt" in user_query_lower:
        return "💳 **Debt Management:** Prioritize paying off high-interest debt (credit cards, payday loans) before investing. Use either the avalanche method (highest interest first) or snowball method (smallest balance first) based on your psychology. Consider debt consolidation for better rates."
    
    elif "emergency" in user_query_lower:
        return "🚨 **Emergency Fund:** Build an emergency fund covering 3-6 months of essential expenses. Keep this in a high-yield savings account for easy access. This prevents you from going into debt when unexpected expenses arise."
    
    else:
        return "💡 **General Financial Advice:** To optimize your finances, follow these steps: 1) Build an emergency fund (3-6 months expenses), 2) Pay off high-interest debt, 3) Max out retirement accounts, 4) Invest in diversified index funds, 5) Consider your risk tolerance and time horizon. Would you like specific advice on any of these areas?"

# Initialize session state
init_session_state()

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
                        title="Monthly Expense Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data available for this month. Please add your expenses to see insights.")
        
        # Show sample if no data
        if st.button("Add Sample Data"):
            sample_expenses = pd.DataFrame({
                'date': [datetime.now() - timedelta(days=x) for x in range(5)],
                'category': ['Food', 'Transportation', 'Rent', 'Utilities', 'Entertainment'],
                'amount': [450, 120, 1500, 200, 85],
                'description': ['Groceries', 'Uber', 'Monthly Rent', 'Electricity', 'Netflix']
            })
            st.session_state.expenses = pd.concat([st.session_state.expenses, sample_expenses], ignore_index=True)
            save_expenses()
            st.success("Sample data added! Refresh to see dashboard.")
            st.rerun()

# Add Expenses
elif page == "Add Expenses":
    st.header("➕ Add New Expense")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now())
            category = st.selectbox("Category", 
                                   ["Food", "Transportation", "Rent", "Utilities", 
                                    "Entertainment", "Shopping", "Healthcare", "Education", "Other"])
        
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.01, step=10.0, value=0.01)
            description = st.text_input("Description", placeholder="e.g., Grocery shopping")
        
        submitted = st.form_submit_button("Add Expense", use_container_width=True)
        
        if submitted:
            new_expense = pd.DataFrame({
                'date': [date],
                'category': [category],
                'amount': [amount],
                'description': [description]
            })
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
            if save_expenses():
                st.success(f"✅ Added ${amount:,.2f} expense for {category}!")
                st.balloons()

# Investment Advisor
elif page == "Investment Advisor":
    st.header("📈 Investment Advisor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_income = st.number_input("Monthly Income ($)", min_value=0, step=500, value=3000)
        monthly_expenses = st.number_input("Monthly Expenses ($)", min_value=0, step=100, value=2000)
    
    with col2:
        risk_tolerance = st.select_slider("Risk Tolerance", 
                                         options=["Low", "Medium", "High"],
                                         value="Medium")
        investment_horizon = st.select_slider("Investment Horizon", 
                                             options=["Short-term (1-3 years)", "Medium-term (3-7 years)", "Long-term (7+ years)"],
                                             value="Medium-term (3-7 years)")
    
    if monthly_income > monthly_expenses:
        monthly_savings = monthly_income - monthly_expenses
        st.success(f"💰 Your monthly savings potential: **${monthly_savings:,.2f}**")
        
        if st.button("Get Investment Suggestions", type="primary"):
            suggestions = suggest_investments(monthly_savings, risk_tolerance)
            
            for suggestion in suggestions:
                st.subheader(f"🎯 Recommended: {suggestion['primary']['type']}")
                
                # Display allocation
                st.write("**Portfolio Allocation:**")
                for asset, percentage in suggestion['primary']['allocation'].items():
                    st.progress(percentage/100, text=f"{asset}: {percentage}%")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Expected Annual Return", f"{suggestion['primary']['expected_return']}%")
                with col2:
                    st.metric("Recommended Duration", f"{suggestion['primary']['min_duration']}-{suggestion['primary']['max_duration']} years")
                with col3:
                    st.metric("Risk Level", suggestion['primary']['risk_level'])
                
                st.info(f"**Recommended Monthly Investment:** ${suggestion['recommended_monthly']:,.2f}")
                st.success(f"**Projected Value after {suggestion['projection_years']} years:** ${suggestion['projected_value']:,.2f}")
                
                # Alternative portfolio
                with st.expander("📊 View Alternative Portfolio"):
                    st.write(f"**Alternative: {suggestion['secondary']['type']}**")
                    st.write(f"Expected Return: {suggestion['secondary']['expected_return']}%")
                    st.write(f"Duration: {suggestion['secondary']['min_duration']}-{suggestion['secondary']['max_duration']} years")
                    st.write(f"Risk: {suggestion['secondary']['risk_level']}")
    else:
        st.error(f"⚠️ You need to reduce expenses or increase income. Current deficit: **${monthly_expenses - monthly_income:,.2f}**")
        st.info("Try to cut non-essential expenses or find ways to increase your income.")

# Budget Planning
elif page == "Budget Planning":
    st.header("🎯 Budget Planner")
    
    current_month = datetime.now().strftime('%Y-%m')
    
    with st.form("budget_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            income = st.number_input("Monthly Income ($)", min_value=0, step=100, value=3000)
        with col2:
            savings_goal = st.number_input("Savings Goal ($)", min_value=0, step=50, value=600)
        with col3:
            investment_goal = st.number_input("Investment Goal ($)", min_value=0, step=50, value=400)
        
        submitted = st.form_submit_button("Save Budget", use_container_width=True)
        
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
            if save_budget():
                st.success(f"✅ Budget saved for {current_month}!")
    
    # Display budget tips
    st.subheader("💡 Financial Planning Tips")
    
    tips = [
        "📊 **50/30/20 Rule:** Allocate 50% to needs, 30% to wants, and 20% to savings",
        "💰 **Automate Savings:** Set up automatic transfers on payday",
        "📉 **Track Expenses:** Use this app to identify spending patterns",
        "🏦 **Emergency Fund:** Build 3-6 months of expenses",
        "📈 **Start Early:** Compound interest works best over long periods",
        "🎯 **Set SMART Goals:** Specific, Measurable, Achievable, Relevant, Time-bound"
    ]
    
    for tip in tips:
        st.info(tip)

# AI Chat
elif page == "AI Chat":
    st.header("🤖 AI Financial Assistant")
    
    st.markdown("Ask me anything about personal finance, investments, or money management!")
    st.caption("💡 Example questions: 'How can I save more money?', 'What should I invest in?', 'How do I plan for retirement?'")
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**🤖 AI Advisor:** {message['content']}")
        st.markdown("---")
    
    # User input
    user_question = st.text_area("Ask your financial question:", height=100, placeholder="e.g., How can I start investing with $500?")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Get Advice", type="primary") and user_question:
            # Prepare financial context
            spending = analyze_spending_patterns()
            financial_data = {
                'monthly_expenses': spending['total'] if spending else 0,
                'savings': st.session_state.budget['savings_goal'].iloc[-1] if len(st.session_state.budget) > 0 else 0,
                'investments': len(st.session_state.investments)
            }
            
            # Get AI response
            with st.spinner("🤔 Analyzing your question..."):
                advice = get_ai_advice(user_question, financial_data)
            
            # Add to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_question})
            st.session_state.chat_history.append({'role': 'assistant', 'content': advice})
            
            st.rerun()
    
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# View History
elif page == "View History":
    st.header("📜 Financial History")
    
    tab1, tab2 = st.tabs(["💰 Expenses", "📈 Investments"])
    
    with tab1:
        if len(st.session_state.expenses) > 0:
            # Add filter
            col1, col2 = st.columns(2)
            with col1:
                date_filter = st.date_input("Filter by date", value=None)
            with col2:
                category_filter = st.multiselect("Filter by category", 
                                                options=st.session_state.expenses['category'].unique())
            
            filtered_df = st.session_state.expenses.copy()
            if date_filter:
                filtered_df = filtered_df[pd.to_datetime(filtered_df['date']).dt.date == date_filter]
            if category_filter:
                filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
            
            st.dataframe(filtered_df.sort_values('date', ascending=False), use_container_width=True)
            
            # Summary statistics
            total_expenses = filtered_df['amount'].sum()
            avg_expense = filtered_df['amount'].mean()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Expenses", f"${total_expenses:,.2f}")
            col2.metric("Average Expense", f"${avg_expense:,.2f}")
            col3.metric("Number of Transactions", len(filtered_df))
            
            if st.button("🗑️ Clear All Expenses", type="secondary"):
                st.session_state.expenses = pd.DataFrame(columns=['date', 'category', 'amount', 'description'])
                save_expenses()
                st.success("All expenses cleared!")
                st.rerun()
        else:
            st.info("No expenses recorded yet. Go to 'Add Expenses' to get started!")
    
    with tab2:
        if len(st.session_state.investments) > 0:
            st.dataframe(st.session_state.investments, use_container_width=True)
            
            total_invested = st.session_state.investments['amount'].sum()
            st.metric("Total Invested", f"${total_invested:,.2f}")
        else:
            st.info("No investments recorded yet. Use the Investment Advisor to get suggestions!")

# Footer
st.markdown("---")
st.markdown("""
    ⚠️ **Disclaimer:** This application is for educational purposes only. 
    The information provided does not constitute financial advice. 
    Always consult with a qualified financial professional before making investment decisions.
""")
.streamlit/secrets.toml (Optional - for OpenAI integration)
toml
# Add your OpenAI API key here if you want real AI responses
# OPENAI_API_KEY = "your-openai-api-key-here"
