from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session

# Dummy user storage (Replace with a real database later)
users = {
    "admin": "admin123",
    "customer": "cust123"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ["admin", "customer"]:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username  # ✅ Store in session

            if role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif role == "customer":
                return redirect(url_for("customer_predictions"))
        else:
            return render_template("login.html", role=role, error="Invalid Credentials!")

    return render_template("login.html", role=role)

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin.html')

@app.route('/charts')
def charts():
    try:
        df = pd.read_csv('predictions.csv')
        if df.empty:
            return "No prediction data available!"

        approval_counts = df["Prediction"].value_counts()
        plt.figure(figsize=(5, 5))
        plt.pie(approval_counts, labels=approval_counts.index, autopct='%1.1f%%', colors=['#4CAF50', '#FF5733'])
        plt.title("Loan Approval vs Rejection")

        pie_io = io.BytesIO()
        plt.savefig(pie_io, format='png')
        pie_io.seek(0)
        pie_chart = base64.b64encode(pie_io.getvalue()).decode()
        plt.close()

        plt.figure(figsize=(6, 4))
        df["ApplicantIncome"] = pd.to_numeric(df["ApplicantIncome"], errors='coerce').dropna()
        plt.hist(df["ApplicantIncome"], bins=20, color="#007bff", alpha=0.7)
        plt.xlabel("Applicant Income")
        plt.ylabel("Frequency")
        plt.title("Income Distribution")

        income_io = io.BytesIO()
        plt.savefig(income_io, format='png')
        income_io.seek(0)
        income_chart = base64.b64encode(income_io.getvalue()).decode()
        plt.close()

        return render_template('charts.html', pie_chart=pie_chart, income_chart=income_chart)

    except Exception as e:
        return f"Error generating charts: {str(e)}"

@app.route('/predictions_data')
def predictions_data():
    try:
        csv_file = 'predictions.csv'
        if not os.path.exists(csv_file):
            return "No prediction data available!"

        df = pd.read_csv(csv_file)

        required_columns = [
            "Timestamp", "Username", "ApplicantName", "DateOfBirth", "Occupation",
            "Gender", "Married", "Dependents", "Education", "Self_Employed",
            "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
            "Credit_History", "Property_Area", "Prediction"
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = "N/A"

        df = df[required_columns]

        return render_template('predictions_table.html', table=df.to_html(classes="styled-table"))

    except Exception as e:
        return f"Error loading predictions: {str(e)}"

@app.route('/customer_predictions', methods=['GET', 'POST'])
def customer_predictions():
    if request.method == 'POST':
        applicant_name = request.form.get('ApplicantName')
        date_of_birth = request.form.get('DateOfBirth')
        occupation = request.form.get('Occupation')
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

        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            today = datetime.today()

            if dob > today:
                prediction = "Rejected"
                feedback = "Date of Birth cannot be in the future."
            else:
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                income = float(applicant_income) + float(coapplicant_income)
                loan_amount = float(loan_amount)
                loan_term = float(loan_term)
                credit_history = int(credit_history)

                # EMI calculation
                interest_rate = 0.08 / 12
                n = loan_term
                emi = (loan_amount * interest_rate * (1 + interest_rate)**n) / (((1 + interest_rate)**n) - 1)

                # DTI calculation
                dti = (emi / income) * 100

                if age < 18 or age > 50:
                    prediction = "Rejected"
                    feedback = "Applicant age must be between 18 and 50."
                elif income < 3000:
                    prediction = "Rejected"
                    feedback = "Combined income must be at least 3000."
                elif dti > 40:
                    prediction = "Rejected"
                    feedback = "Debt-to-Income (DTI) ratio exceeds 40%."
                elif credit_history != 1:
                    prediction = "Rejected"
                    feedback = "Credit history must be good (value should be 1)."
                else:
                    prediction = "Approved"
                    feedback = "Loan approved based on age, income, DTI, and credit history."
        except Exception as e:
            prediction = "Error"
            feedback = f"Input error: {str(e)}"

        # Save prediction
        csv_file = "predictions.csv"
        file_exists = os.path.exists(csv_file)

        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Timestamp", "Username", "ApplicantName", "DateOfBirth", "Occupation",
                    "Gender", "Married", "Dependents", "Education", "Self_Employed",
                    "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
                    "Credit_History", "Property_Area", "Prediction", "Feedback"
                ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                session.get("username", "Unknown"),
                applicant_name, date_of_birth, occupation,
                gender, married, dependents, education, self_employed,
                applicant_income, coapplicant_income, loan_amount, loan_term,
                credit_history, property_area, prediction, feedback
            ])

        return render_template('result.html', prediction=prediction, feedback=feedback)

    max_date = datetime.today().strftime('%Y-%m-%d')
    return render_template('customer_predictions.html', max_date=max_date)


@app.route('/customer_history')
def customer_history():
    username = session.get("username", None)
    if not username:
        return redirect(url_for("login", role="customer"))

    try:
        df = pd.read_csv("predictions.csv")
        df = df[df["Username"] == username]  # ✅ Filter only their predictions

        if df.empty:
            return "No loan predictions found for you."

        df = df.drop(columns=["Username"])

        return render_template("customer_history.html", table=df.to_html(classes="styled-table"))

    except Exception as e:
        return f"Error loading your history: {str(e)}"

@app.route('/customer_details')
def customer_details():
    csv_file = 'customers.csv'
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=['Username', 'Password'])

    customer_count = len(df)
    return render_template('customer_details.html', customers=df.to_dict(orient='records'), customer_count=customer_count)

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return render_template("register_customer.html", error="Username already exists!")

        users[username] = password

        csv_file = 'customers.csv'
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Username', 'Password'])
            writer.writerow([username, password])

        return redirect(url_for('login', role='customer'))

    return render_template('register_customer.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop("username", None)
    return redirect(url_for('login', role='admin'))

@app.route('/customer_logout')
def customer_logout():
    session.pop("username", None)  # ✅ Clear session
    return redirect(url_for('login', role='customer'))

if __name__ == "__main__":
    app.run(debug=True)
