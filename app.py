from flask import Flask, render_template, request
import joblib
import numpy as np
import os

app = Flask(__name__)

# Load trained model
model_path = os.path.join(os.getcwd(), "model", "loan_model.pkl")
print("Loading model from:", model_path)

try:
    model = joblib.load(model_path)
except FileNotFoundError:
    print("Error: Model file not found!")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.form
    features = np.array([
        int(data['Gender']),
        int(data['Married']),
        int(data['Dependents']), 
        int(data['Education']),
        int(data['Self_Employed']),
        float(data['ApplicantIncome']),
        float(data['CoapplicantIncome']),
        float(data['LoanAmount']),
        float(data['Loan_Amount_Term']),
        float(data['Credit_History']),
        int(data['Property_Area'])
    ]).reshape(1, -1)

    prediction = model.predict(features)[0]
    result = "Approved" if prediction == 1 else "Rejected"
    
    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
