# ✅ Import necessary libraries
from flask import Flask, render_template, request, jsonify, send_file
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import os
from datetime import datetime
from io import BytesIO
import base64

# ✅ Initialize Flask App
app = Flask(__name__)
print("✅ Flask App is Starting...")

# ✅ Load Model and Scaler
model_path = os.path.join(os.getcwd(), "model", "loan_model.pkl")
scaler_path = os.path.join(os.getcwd(), "model", "scaler.pkl")

try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print("✅ Model and Scaler loaded successfully!")
except FileNotFoundError as e:
    print("❌ Error loading files:", e)

# ✅ Define the correct feature order (11 features)
FEATURES = [
    'Gender', 'Married', 'Dependents', 'Education', 'Self_Employed',
    'ApplicantIncome', 'CoapplicantIncome', 'LoanAmount',
    'Loan_Amount_Term', 'Credit_History', 'Property_Area'
]

# ✅ Path to store predictions
predictions_file = os.path.join(os.getcwd(), "predictions.csv")

# ========================================
# ✅ Home Page Route
@app.route('/')
def home():
    print("✅ Home Page Accessed")
    return render_template('home.html')


# ========================================
# ✅ Prediction Page Route (GET and POST)
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        print("✅ Prediction Page Accessed")
        return render_template('index.html')

    elif request.method == 'POST':
        try:
            # 🧑‍💻 Extract form data
            data = request.form
            print("✅ Received Data:", data)

            # 🧑‍💻 Collect input features in the correct order (11 features)
            input_features = []
            for feature in FEATURES:
                input_features.append(float(data[feature]))

            # 🧑‍💻 Add 3 dummy features to match scaler's 14 expected features
            dummy_features = [0, 0, 0]
            input_with_dummy = input_features + dummy_features

            # 🧑‍💻 Reshape input, scale, and select only 11 features for the model
            input_array = np.array(input_with_dummy).reshape(1, -1)
            print("✅ Input Features (14):", input_array)

            # ✅ Scale input
            scaled_input = scaler.transform(input_array)
            scaled_input_11 = scaled_input[:, :11]  # Select only first 11 features

            # ✅ Make prediction with 11 features
            prediction = model.predict(scaled_input_11)[0]
            result = "Approved" if prediction == 1 else "Rejected"
            print("✅ Prediction Result:", result)

            # ✅ Store the prediction in predictions.csv
            prediction_data = [str(datetime.now())] + input_features + [result]
            header = ['Timestamp'] + FEATURES + ['Prediction']

            # Create CSV if not exists and write the header
            if not os.path.exists(predictions_file):
                with open(predictions_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)

            # Append new prediction
            with open(predictions_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(prediction_data)

            # ✅ Return result
            return render_template('result.html', prediction=result)

        except Exception as e:
            print("❌ Prediction Error:", str(e))
            return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# ========================================
# ✅ View Predictions Route
@app.route('/view-predictions', methods=['GET'])
def view_predictions():
    try:
        # Check if predictions file exists
        if not os.path.exists(predictions_file):
            return "<h2>No predictions found.</h2>"

        # Read the predictions from CSV
        with open(predictions_file, 'r') as f:
            predictions = [line.strip().split(',') for line in f]

        # Render predictions table
        return render_template('predictions.html', predictions=predictions)

    except Exception as e:
        print("❌ Error:", str(e))
        return f"<h2>Error loading predictions: {str(e)}</h2>"


# ========================================
# ✅ Charts Page Route (No Duplicates)
@app.route('/charts')
def charts():
    try:
        # Check if predictions file exists
        if not os.path.exists(predictions_file):
            return "<h2>No predictions found.</h2>"

        # Load predictions into DataFrame
        df = pd.read_csv(predictions_file)

        # Convert predictions to numeric (1 = Approved, 0 = Rejected)
        df['Prediction'] = df['Prediction'].apply(lambda x: 1 if x == 'Approved' else 0)
        df['Prediction'] = df['Prediction'].map({0: 'Rejected', 1: 'Approved'})

        # ✅ Approval vs Rejection (Pie Chart)
        approval_counts = df['Prediction'].value_counts()
        pie_chart = BytesIO()
        plt.figure(figsize=(6, 6))
        plt.pie(approval_counts, labels=['Rejected', 'Approved'], autopct='%1.1f%%', colors=['#FF6F61', '#6BDF7B'])
        plt.title('Approval vs Rejection Rate', fontsize=14)
        plt.savefig(pie_chart, format='png')
        pie_chart.seek(0)
        pie_chart_base64 = base64.b64encode(pie_chart.read()).decode('utf-8')
        plt.close()

        # ✅ Income Distribution (Once)
        income_chart = BytesIO()
        plt.figure(figsize=(8, 5))
        sns.histplot(data=df, x='ApplicantIncome', kde=True, hue='Prediction', palette={'Rejected': '#FF6F61', 'Approved': '#6BDF7B'})
        plt.title('Income Distribution', fontsize=14)
        plt.xlabel('Applicant Income')
        plt.ylabel('Frequency')
        plt.savefig(income_chart, format='png')
        income_chart.seek(0)
        income_chart_base64 = base64.b64encode(income_chart.read()).decode('utf-8')
        plt.close()

        # ✅ Render the charts.html page with images
        return render_template('charts.html',
                               pie_chart=pie_chart_base64,
                               income_chart=income_chart_base64)

    except Exception as e:
        print("❌ Error Generating Charts:", str(e))
        return f"<h2>Error generating charts: {str(e)}</h2>"


# ========================================
# ✅ Download Predictions Route
@app.route('/download-predictions', methods=['GET'])
def download_predictions():
    try:
        # Check if predictions file exists
        if os.path.exists(predictions_file):
            return send_file(predictions_file, as_attachment=True)
        else:
            return "<h2>No predictions found to download.</h2>"

    except Exception as e:
        print("❌ Error:", str(e))
        return f"<h2>Error downloading predictions: {str(e)}</h2>"


# ========================================
# ✅ Run the app with Render Port Fix
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))  # Use PORT from Render, fallback to 10000 locally
    print(f"✅ App is Running on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
