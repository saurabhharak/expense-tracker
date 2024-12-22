import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
# Set page configuration
st.set_page_config(page_title="Jijau Home Expense Tracker", page_icon="🏗️", layout="wide")
# Apply custom styles
st.markdown(
    """
    <style>
        body {
            background-color: #f5f5f5;
        }
        .main-header {
            font-size: 2rem;
            color: #4CAF50;
            text-align: center;
            margin-bottom: 1rem;
        }
        .section-header {
            font-size: 1.5rem;
            color: #2196F3;
            margin-top: 2rem;
        }
        .metric-container {
            display: flex;
            justify-content: space-around;
            margin: 1rem 0;
        }
        .metric {
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            background: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Database connection
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        description TEXT,
        total_amount REAL,
        paid_amount REAL,
        quantity INTEGER
    )
    """
)
conn.commit()

# Function to fetch expenses from the database
def fetch_expenses():
    query = "SELECT * FROM expenses"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    return df

# Function to insert a new expense into the database
def add_expense(expense):
    cursor.execute(
        """
        INSERT INTO expenses (date, category, description, total_amount, paid_amount, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            expense["Date"],
            expense["Category"],
            expense["Description"],
            expense["Total Amount"],
            expense["Paid Amount"],
            expense["Quantity"],
        ),
    )
    conn.commit()

# Function to delete an expense by ID
def delete_expense(expense_id):
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()

# Sidebar: Add Expense Form
st.sidebar.header("💵 Add Expense")
expense_date = st.sidebar.date_input("Date", date.today())
category_options = [
    "Architect & Structural Consulting",
    "Bore Well",
    "Cement",
    "Cement/Clay Blocks",
    "Deposits/Refundable",
    "Earth Work",
    "Electrical",
    "Flooring",
    "Interior",
]
category = st.sidebar.selectbox("Category", category_options + ["Other"])
if category == "Other":
    category = st.sidebar.text_input("Enter New Category", "")

description = st.sidebar.text_input("Description", "")
total_amount = st.sidebar.number_input("Total Amount", min_value=0.0, step=0.01)
paid_amount = st.sidebar.number_input("Amount Paid", min_value=0.0, max_value=total_amount, step=0.01)
quantity = st.sidebar.number_input("Quantity", min_value=1, step=1)

if st.sidebar.button("Save Expense"):
    new_expense = {
        "Date": expense_date,
        "Category": category,
        "Description": description,
        "Total Amount": total_amount,
        "Paid Amount": paid_amount,
        "Quantity": quantity,
    }
    add_expense(new_expense)
    st.sidebar.success("Expense added successfully!")

# Main Dashboard
st.markdown("<div class='main-header'>🏠 Jijau Home Construction Expense Tracker</div>", unsafe_allow_html=True)

# Metrics Section
st.markdown("<div class='section-header'>📊 Metrics</div>", unsafe_allow_html=True)
expenses = fetch_expenses()
if not expenses.empty:
    total_expense = expenses["total_amount"].sum()
    incomplete_payments = (expenses["total_amount"] - expenses["paid_amount"]).sum()
    col1, col2 = st.columns(2)
    col1.metric("Total Expenses", f"\u20B9{total_expense:,.2f}")
    col2.metric("Incomplete Payments", f"\u20B9{incomplete_payments:,.2f}")

    # Summary by Category
    st.markdown("<div class='section-header'>📑 Summary by Category</div>", unsafe_allow_html=True)
    category_summary = expenses.groupby("category").agg(
        {
            "total_amount": "sum",
            "paid_amount": "sum",
        }
    )
    category_summary["remaining_amount"] = category_summary["total_amount"] - category_summary["paid_amount"]
    category_summary.rename(
        columns={
            "total_amount": "Total Amount",
            "paid_amount": "Paid Amount",
            "remaining_amount": "Remaining Amount",
        },
        inplace=True,
    )
    st.dataframe(category_summary.reset_index(), use_container_width=True)
else:
    st.write("No expenses added yet!")
    st.metric("Total Expenses", "\u20B90.00")
    st.metric("Incomplete Payments", "\u20B90.00")

# Improved Expense Table
st.markdown("<div class='section-header'>📜 Expense Details</div>", unsafe_allow_html=True)
if not expenses.empty:
    expenses["remaining_amount"] = expenses["total_amount"] - expenses["paid_amount"]
    st.dataframe(
    expenses.rename(columns={
        'date': 'Date',
        'category': 'Category',
        'description': 'Description',
        'total_amount': 'Total Amount',
        'paid_amount': 'Paid Amount',
        'quantity': 'Quantity',
        'remaining_amount': 'Remaining Amount'
    }).drop(columns=["id"]),
    use_container_width=True
)
    expense_ids = expenses["id"].tolist()
    selected_expense_id = st.selectbox("Select Expense ID to Delete", options=[None] + expense_ids)
    if selected_expense_id and st.button("Delete Expense"):
        delete_expense(selected_expense_id)
        st.success("Expense deleted successfully!")
else:
    st.write("No expenses to display.")

# Filtering by Date and Category
st.markdown("<div class='section-header'>🔎 Filter Expenses</div>", unsafe_allow_html=True)
start_date = st.date_input("Start Date", date.today())
end_date = st.date_input("End Date", date.today())
selected_category = st.selectbox("Filter by Category", options=["All"] + category_options)

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

if not expenses.empty:
    filtered_expenses = expenses[(expenses["date"] >= start_date) & (expenses["date"] <= end_date)]
    if selected_category != "All":
        filtered_expenses = filtered_expenses[filtered_expenses["category"] == selected_category]
    st.dataframe(filtered_expenses, use_container_width=True)
else:
    st.write("No expenses to display for the selected filters.")

# Pie Chart for Category Breakdown
st.markdown("<div class='section-header'>📊 Category-Wise Breakdown</div>", unsafe_allow_html=True)
if not expenses.empty:
    fig1, ax1 = plt.subplots()
    category_summary = expenses.groupby("category")["total_amount"].sum()
    ax1.pie(
        category_summary,
        labels=category_summary.index,
        autopct="%1.1f%%",
        startangle=90
    )
    ax1.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig1)

# Close database connection on app exit
import atexit

def close_connection():
    conn.close()

atexit.register(close_connection)
