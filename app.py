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

# Sidebar: Entry Mode
st.sidebar.header("💵 Add Expense")
entry_mode = st.sidebar.radio("Choose Entry Type", ["New Entry", "Use Existing Category"])

if entry_mode == "New Entry":
    # New Entry Form
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

elif entry_mode == "Use Existing Category":
    # Use Existing Category
    st.sidebar.subheader("Deduct from Existing Category")
    expenses = fetch_expenses()
    existing_categories = expenses[expenses["total_amount"] > expenses["paid_amount"]]["category"].unique()

    if len(existing_categories) > 0:
        selected_category = st.sidebar.selectbox("Select Category", options=existing_categories)
        deduction_date = st.sidebar.date_input("Date", date.today())
        deduction_description = st.sidebar.text_input("Description", "")
        deduction_amount = st.sidebar.number_input("Amount to Deduct", min_value=0.0, step=0.01)
        deduction_quantity = st.sidebar.number_input("Quantity", min_value=1, step=1)

        if st.sidebar.button("Save Deduction"):
            # Add a new record for the deduction
            deduction_expense = {
                "Date": deduction_date,
                "Category": selected_category,
                "Description": deduction_description,
                "Total Amount": 0,  # No additional total cost for deduction
                "Paid Amount": deduction_amount,
                "Quantity": deduction_quantity,
            }
            add_expense(deduction_expense)
            st.sidebar.success(f"₹{deduction_amount:,.2f} deducted from {selected_category} and recorded successfully!")
    else:
        st.sidebar.write("No categories with remaining amounts available.")

# Main Dashboard
st.markdown("<div class='main-header'>🏠 Jijau Home Construction Expense Tracker</div>", unsafe_allow_html=True)

# Metrics Section
st.markdown("<div class='section-header'>📊 Metrics</div>", unsafe_allow_html=True)
expenses = fetch_expenses()
if not expenses.empty:
    total_expense = expenses.groupby("category")["total_amount"].sum().sum()
    paid_amount = expenses.groupby("category")["paid_amount"].sum().sum()
    incomplete_payments = total_expense - paid_amount
    col1, col2 = st.columns(2)
    col1.metric("Total Expenses", f"₹{total_expense:,.2f}")
    col2.metric("Incomplete Payments", f"₹{incomplete_payments:,.2f}")

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
    st.metric("Total Expenses", "₹0.00")
    st.metric("Incomplete Payments", "₹0.00")

# Improved Expense Table
st.markdown("<div class='section-header'>📜 Expense Details</div>", unsafe_allow_html=True)
if not expenses.empty:
    st.dataframe(
        expenses.rename(columns={
            'date': 'Date',
            'category': 'Category',
            'description': 'Description',
            'total_amount': 'Total Amount',
            'paid_amount': 'Paid Amount',
            'quantity': 'Quantity',
        }).drop(columns=["id"]),
        use_container_width=True
    )
else:
    st.write("No expenses to display.")

# Filtering by Date and Category
st.markdown("<div class='section-header'>🔎 Filter Expenses</div>", unsafe_allow_html=True)
start_date = st.date_input("Start Date", date.today())
end_date = st.date_input("End Date", date.today())
selected_category = st.selectbox("Filter by Category", options=["All"] + [
    "Architect & Structural Consulting",
    "Bore Well",
    "Cement",
    "Cement/Clay Blocks",
    "Deposits/Refundable",
    "Earth Work",
    "Electrical",
    "Flooring",
    "Interior",
])

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
