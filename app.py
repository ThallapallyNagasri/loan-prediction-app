# ✅ Import necessary libraries
from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import csv
import os
from datetime import datetime

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
# ✅ Run the app with Render Port Fix
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))  # Use PORT from Render, fallback to 10000 locally
    print(f"✅ App is Running on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
