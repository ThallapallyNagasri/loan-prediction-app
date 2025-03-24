from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import csv
import os
from datetime import datetime  # For Timestamp
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Dummy user storage (Replace with a real database later)
users = {
    "admin": "admin123",  # Default Admin
    "customer": "cust123"  # Default Customer
}

@app.route('/')
def index():
    return render_template('index.html')

# Welcome Page
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

# Login Page for Admin/Customer
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ["admin", "customer"]:
        return redirect(url_for("home"))  # Redirect if role is invalid

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user exists and password matches
        if username in users and users[username] == password:
            if role == "admin":
                return redirect(url_for("admin_dashboard"))  # Redirect to Admin Page
            elif role == "customer":
                return redirect(url_for("customer_predictions"))  # Redirect to Customer Page
        else:
            return render_template("login.html", role=role, error="Invalid Credentials!")

    return render_template("login.html", role=role)

# **Admin Dashboard**
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin.html')

# **Charts Page (Analyze Predictions)**
@app.route('/charts')
def charts():
    try:
        df = pd.read_csv('predictions.csv')

        # Ensure data exists
        if df.empty:
            return "No prediction data available!"

        # **1. Loan Approval vs Rejection Pie Chart**
        approval_counts = df["Prediction"].value_counts()
        plt.figure(figsize=(5, 5))
        plt.pie(approval_counts, labels=approval_counts.index, autopct='%1.1f%%', colors=['#4CAF50', '#FF5733'])
        plt.title("Loan Approval vs Rejection")

        # Save as base64
        pie_io = io.BytesIO()
        plt.savefig(pie_io, format='png')
        pie_io.seek(0)
        pie_chart = base64.b64encode(pie_io.getvalue()).decode()
        plt.close()

        # **2. Income Distribution Histogram**
        plt.figure(figsize=(6, 4))
        df["ApplicantIncome"] = pd.to_numeric(df["ApplicantIncome"], errors='coerce').dropna()
        plt.hist(df["ApplicantIncome"], bins=20, color="#007bff", alpha=0.7)
        plt.xlabel("Applicant Income")
        plt.ylabel("Frequency")
        plt.title("Income Distribution")

        # Save as base64
        income_io = io.BytesIO()
        plt.savefig(income_io, format='png')
        income_io.seek(0)
        income_chart = base64.b64encode(income_io.getvalue()).decode()
        plt.close()

        return render_template('charts.html', pie_chart=pie_chart, income_chart=income_chart)

    except Exception as e:
        return f"Error generating charts: {str(e)}"

# **Predictions Data Page (Displays predictions.csv)**
# **Predictions Data Page (Displays predictions.csv)**
# **Predictions Data Page (Displays predictions.csv)**
@app.route('/predictions_data')
def predictions_data():
    try:
        # Load the predictions CSV
        csv_file = 'predictions.csv'
        if not os.path.exists(csv_file):
            return "No prediction data available!"

        # Read CSV and ensure proper columns
        df = pd.read_csv(csv_file)

        # Required columns (with new fields)
        required_columns = [
            "Timestamp", "ApplicantName", "DateOfBirth", "Occupation",
            "Gender", "Married", "Dependents", "Education", "Self_Employed",
            "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
            "Credit_History", "Property_Area", "Prediction"
        ]

        # Add missing columns in old predictions with "N/A"
        for col in required_columns:
            if col not in df.columns:
                df[col] = "N/A"

        # Ensure the columns are ordered correctly
        df = df[required_columns]

        # Convert DataFrame to HTML and send it to the predictions table
        return render_template('predictions_table.html', table=df.to_html(classes="styled-table"))

    except Exception as e:
        return f"Error loading predictions: {str(e)}"



# **Customer Predictions Page**
# **Customer Predictions Page**
@app.route('/customer_predictions', methods=['GET', 'POST'])
def customer_predictions():
    if request.method == 'POST':
        # Get new input fields
        applicant_name = request.form.get('ApplicantName')
        date_of_birth = request.form.get('DateOfBirth')
        occupation = request.form.get('Occupation')

        # Existing fields (keep them unchanged)
        gender = request.form.get('Gender')
        married = request.form.get('Married')
        dependents = request.form.get('Dependents')
        education = request.form.get('Education')
        self_employed = request.form.get('Self_Employed')
        applicant_income = request.form.get('ApplicantIncome')
        coapplicant_income = request.form.get('CoapplicantIncome')
        loan_amount = request.form.get('LoanAmount')
        loan_term = request.form.get('Loan_Amount_Term')
        credit_history = request.form.get('Credit_History')
        property_area = request.form.get('Property_Area')

        # Dummy ML model prediction (Replace with real model)
        prediction = "Approved" if int(credit_history) == 1 else "Rejected"

        # Store prediction in predictions.csv
        csv_file = "predictions.csv"
        file_exists = os.path.exists(csv_file)

        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)

            # Ensure header exists for new fields
            if not file_exists:
                writer.writerow([
                    "Timestamp", "ApplicantName", "DateOfBirth", "Occupation",
                    "Gender", "Married", "Dependents", "Education", "Self_Employed",
                    "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
                    "Credit_History", "Property_Area", "Prediction"
                ])

            # Append prediction with new fields
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                applicant_name, date_of_birth, occupation,
                gender, married, dependents, education, self_employed,
                applicant_income, coapplicant_income, loan_amount, loan_term,
                credit_history, property_area, prediction
            ])

        return render_template('result.html', prediction=prediction)

    return render_template('customer_predictions.html')


    
@app.route('/customer_details')
def customer_details():
    csv_file = 'customers.csv'
    
    # Check if the file exists and load customer data
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=['Username', 'Password'])

    customer_count = len(df)
    
    return render_template('customer_details.html', customers=df.to_dict(orient='records'), customer_count=customer_count)


# **Customer Registration Page**
@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return render_template("register_customer.html", error="Username already exists!")
        
        # Store in users dictionary (temporary)
        users[username] = password
        
        # Append to CSV file
        csv_file = 'customers.csv'
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Username', 'Password'])
            writer.writerow([username, password])

        return redirect(url_for('login', role='customer'))  # Redirect to login after registering

    return render_template('register_customer.html')

# **Logout Routes**
@app.route('/admin_logout')
def admin_logout():
    return redirect(url_for('login', role='admin'))

@app.route('/customer_logout')
def customer_logout():
    return redirect(url_for('login', role='customer'))

if __name__ == "__main__":
    app.run(debug=True)
