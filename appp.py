from flask import Flask, render_template, request, jsonify
import numpy as np
import joblib

app = Flask(__name__)

# Load trained SVM model and the scaler
model = joblib.load('model/diabetes_model.pkl')
scaler = joblib.load('model/scaler.pkl')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()

    # Extract and order input features
    features = np.array([[
        data['pregnancies'], data['glucose'], data['bloodPressure'],
        data['skinThickness'], data['insulin'], data['bmi'],
        data['diabetesPedigree'], data['age']
    ]])

    # Apply scaling
    features_scaled = scaler.transform(features)

    # Make prediction
    prediction = model.predict(features_scaled)[0]

    return jsonify({'prediction': int(prediction)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
