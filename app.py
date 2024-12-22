import streamlit as st
import pandas as pd
import sqlitecloud
import matplotlib.pyplot as plt
from datetime import date
import toml

# ----------------------------------------
# 1. PAGE CONFIGURATION + STYLES
# ----------------------------------------
st.set_page_config(page_title="Jijau Home Expense Tracker", page_icon="🏗️", layout="wide")

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

# ----------------------------------------
# 2. LOAD CONFIG
# ----------------------------------------
with open("config.toml", "r") as f:
    config = toml.load(f)

DATABASE_URL = config["database"]["url"]

# ----------------------------------------
# 3. DATABASE CONNECTION
# ----------------------------------------
conn = sqlitecloud.connect(DATABASE_URL)
cursor = conn.cursor()
# Replace `chinook.sqlite` with your actual database name
cursor.execute("USE DATABASE chinook.sqlite;")  

# ----------------------------------------
# 4. HELPER FUNCTIONS
# ----------------------------------------

def column_exists(table_name, column_name):
    """
    Checks if a column exists in a table in the current SQLiteCloud database.
    """
    query = f"PRAGMA table_info({table_name});"
    cursor.execute(query)
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


# Create the expenses table if it doesn't exist
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
    );
    """
)
conn.commit()

# Add the `paid_by` column if it doesn't already exist
if not column_exists("expenses", "paid_by"):
    cursor.execute("ALTER TABLE expenses ADD COLUMN paid_by TEXT;")
    conn.commit()


def fetch_expenses():
    """
    Fetches all expenses from the database as a pandas DataFrame.
    """
    query = "SELECT * FROM expenses"
    df = pd.read_sql(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    return df


def add_expense(expense):
    """
    Inserts a new expense record (including `paid_by`) into the database.
    """
    query = """
        INSERT INTO expenses (date, category, description, total_amount, paid_amount, quantity, paid_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        expense["Date"].strftime("%Y-%m-%d"),
        expense["Category"],
        expense["Description"],
        expense["Total Amount"],
        expense["Paid Amount"],
        expense["Quantity"],
        expense["Paid By"],
    )
    cursor.execute(query, params)
    conn.commit()


def delete_expense(expense_id):
    """
    Deletes the expense with the given ID from the database.
    """
    query = "DELETE FROM expenses WHERE id = ?"
    cursor.execute(query, (expense_id,))
    conn.commit()

# ----------------------------------------
# 5. SIDEBAR: ADDING / DEDUCTING / DELETING EXPENSES
# ----------------------------------------
st.sidebar.header("💵 Manage Expenses")
entry_mode = st.sidebar.radio(
    "Choose Action",
    ["New Entry", "Use Existing Category", "Delete Expense"]
)

if entry_mode == "New Entry":
    # -- New Entry Form --
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
    paid_by = st.sidebar.selectbox("Paid By", ["Saurabh Harak", "DK&NK Brothers"])

    if st.sidebar.button("Save Expense"):
        if paid_amount > total_amount:
            st.sidebar.error("Paid Amount cannot exceed Total Amount.")
        else:
            new_expense = {
                "Date": expense_date,
                "Category": category,
                "Description": description,
                "Total Amount": total_amount,
                "Paid Amount": paid_amount,
                "Quantity": quantity,
                "Paid By": paid_by,
            }
            add_expense(new_expense)
            st.sidebar.success("Expense added successfully!")

elif entry_mode == "Use Existing Category":
    # -- Deduct from existing category --
    st.sidebar.subheader("Deduct from Existing Category")
    expenses_df = fetch_expenses()
    # Only categories which still have unpaid balances
    existing_categories = expenses_df[expenses_df["total_amount"] > expenses_df["paid_amount"]]["category"].unique()

    if len(existing_categories) > 0:
        selected_category = st.sidebar.selectbox("Select Category", options=existing_categories)
        deduction_date = st.sidebar.date_input("Date", date.today())
        deduction_description = st.sidebar.text_input("Description", "")
        deduction_amount = st.sidebar.number_input("Amount to Deduct", min_value=0.0, step=0.01)
        deduction_quantity = st.sidebar.number_input("Quantity", min_value=1, step=1)
        paid_by = st.sidebar.selectbox("Paid By", ["Saurabh Harak", "DK&NK Brothers"])

        if st.sidebar.button("Save Deduction"):
            # Add a new record for the deduction
            deduction_expense = {
                "Date": deduction_date,
                "Category": selected_category,
                "Description": deduction_description,
                "Total Amount": 0.0,  # No additional total cost for deduction
                "Paid Amount": deduction_amount,
                "Quantity": deduction_quantity,
                "Paid By": paid_by,
            }
            add_expense(deduction_expense)
            st.sidebar.success(
                f"₹{deduction_amount:,.2f} deducted from '{selected_category}' and recorded successfully!"
            )
    else:
        st.sidebar.write("No categories with remaining amounts available.")

elif entry_mode == "Delete Expense":
    st.sidebar.subheader("Delete an Expense")
    all_expenses = fetch_expenses()
    if not all_expenses.empty:
        # Convert ID to string for display
        expense_ids = [str(x) for x in all_expenses["id"].tolist()]
        selected_id = st.sidebar.selectbox("Select Expense ID to Delete", expense_ids)

        if st.sidebar.button("Delete Expense"):
            delete_expense(selected_id)
            st.sidebar.success(f"Expense with ID {selected_id} deleted successfully!")
    else:
        st.sidebar.write("No expenses available to delete.")


# ----------------------------------------
# 6. MAIN DASHBOARD HEADER
# ----------------------------------------
st.markdown("<div class='main-header'>🏠 Jijau Home Construction Expense Tracker</div>", unsafe_allow_html=True)
expenses = fetch_expenses()

# ----------------------------------------
# 7. METRICS SECTION
# ----------------------------------------
st.markdown("<div class='section-header'>📊 Expenses</div>", unsafe_allow_html=True)

if not expenses.empty:
    total_expense = expenses["total_amount"].sum()
    total_paid = expenses["paid_amount"].sum()
    incomplete_payments = total_expense - total_paid
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Expenses", f"₹{total_expense:,.2f}")
    col2.metric("Total Paid", f"₹{total_paid:,.2f}")
    col3.metric("Pending Payments", f"₹{incomplete_payments:,.2f}")
else:
    st.metric("Total Expenses", "₹0.00")
    st.metric("Total Paid", "₹0.00")
    st.metric("Pending Payments", "₹0.00")

# ----------------------------------------
# 8. SUMMARY BY CATEGORY
# ----------------------------------------
st.markdown("<div class='section-header'>📑 Summary by Category</div>", unsafe_allow_html=True)
if not expenses.empty:
    category_summary = expenses.groupby("category").agg(
        {"total_amount": "sum", "paid_amount": "sum"}
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

# ----------------------------------------
# 9. EXPENSE DETAILS TABLE
# ----------------------------------------
st.markdown("<div class='section-header'>📜 Expense Details</div>", unsafe_allow_html=True)
if not expenses.empty:
    display_df = expenses.rename(
        columns={
            'id': 'ID',
            'date': 'Date',
            'category': 'Category',
            'description': 'Description',
            'total_amount': 'Total Amount',
            'paid_amount': 'Paid Amount',
            'quantity': 'Quantity',
            'paid_by': 'Paid By',
        }
    )
    st.dataframe(display_df, use_container_width=True)
else:
    st.write("No expenses to display.")

# ----------------------------------------
# 10. FILTERING BY DATE AND CATEGORY
# ----------------------------------------
st.markdown("<div class='section-header'>🔎 Filter Expenses</div>", unsafe_allow_html=True)
start_date = st.date_input("Start Date", date.today())
end_date = st.date_input("End Date", date.today())

if not expenses.empty:
    # We'll provide a sorted list of categories for the filter
    all_categories = ["All"] + sorted(expenses["category"].unique())
    filter_category = st.selectbox("Filter by Category", options=all_categories)

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    filtered_expenses = expenses[
        (expenses["date"] >= start_date) & (expenses["date"] <= end_date)
    ]
    if filter_category != "All":
        filtered_expenses = filtered_expenses[filtered_expenses["category"] == filter_category]

    st.dataframe(filtered_expenses, use_container_width=True)
else:
    st.write("No expenses to display for the selected filters.")

# ----------------------------------------
# 11. PIE CHARTS
# ----------------------------------------
st.markdown("<div class='section-header'>📊 Category-Wise Breakdown</div>", unsafe_allow_html=True)
if not expenses.empty:
    # Pie Chart for Total Amount by Category
    fig1, ax1 = plt.subplots()
    total_amount_summary = expenses.groupby("category")["total_amount"].sum()
    ax1.pie(
        total_amount_summary,
        labels=total_amount_summary.index,
        autopct="%1.1f%%",
        startangle=90
    )
    ax1.set_title("Total Amount Breakdown")
    ax1.axis("equal") 
    st.pyplot(fig1)

    # Pie Chart for Paid Amount by Category
    fig2, ax2 = plt.subplots()
    paid_summary = expenses.groupby("category")["paid_amount"].sum()
    ax2.pie(
        paid_summary,
        labels=paid_summary.index,
        autopct=lambda p: f"₹{p * paid_summary.sum() / 100:.2f}",
        startangle=90
    )
    ax2.set_title("Paid Amount Breakdown")
    ax2.axis("equal")
    st.pyplot(fig2)

# ----------------------------------------
# 12. CLOSE DB CONNECTION ON APP EXIT
# ----------------------------------------
import atexit

def close_connection():
    conn.close()

atexit.register(close_connection)
