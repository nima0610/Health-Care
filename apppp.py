from flask import Flask, render_template, request, jsonify
import pickle
import joblib
import numpy as np

app = Flask(__name__)

# Load all models and scalers
with open('svm_model.pkl', 'rb') as f:
    illness_model = pickle.load(f)

# Load diabetes model and scaler (from either structure)
try:
    diabetes_model = joblib.load('model/diabetes_model.pkl')
    diabetes_scaler = joblib.load('model/scaler.pkl')
except:
    diabetes_model = pickle.load(open('diabetes_svm_model.pkl', 'rb'))
    diabetes_scaler = pickle.load(open('diabetes_scaler.pkl', 'rb'))

# Symptom-based illness prediction data
symptoms_list = [
    'fever', 'headache', 'eye pain', 'cough', 'sneezing', 'nasal congestion',
    'sore throat', 'runny nose', 'fatigue', 'body ache', 'joint pain',
    'diarrhea', 'vomiting', 'abdominal pain', 'nausea', 'rash',
    'shortness of breath', 'loss of taste and smell'
]

precautions_dict = {
    'diabetes': [
        'Maintain a balanced diet', 'Exercise regularly',
        'Monitor blood sugar levels', 'Take medication as prescribed',
        'Avoid excessive sugar intake'
    ],
    'flu': [
        'Get plenty of rest', 'Drink fluids to stay hydrated',
        'Take antiviral medications if prescribed',
        'Cover your mouth when coughing or sneezing',
        'Avoid close contact with others to prevent spreading'
    ],
    'cold': [
        'Rest well', 'Stay hydrated', 'Use saline nasal sprays to relieve congestion',
        'Avoid smoking and alcohol', 'Practice good hygiene like hand washing'
    ],
    'malaria': [
        'Use mosquito nets and repellents', 'Avoid mosquito-prone areas',
        'Take antimalarial medication as prescribed', 'Wear protective clothing',
        'Drain standing water to reduce mosquito breeding sites'
    ],
    'dengue': [
        'Use mosquito repellents and nets', 'Avoid mosquito bites, especially during daytime',
        'Stay hydrated', 'Rest and avoid strenuous activity',
        'Seek medical attention if symptoms worsen'
    ],
    'covid-19': [
        'Wear masks in crowded places', 'Maintain social distancing',
        'Wash hands frequently', 'Get vaccinated',
        'Isolate if symptomatic or tested positive'
    ]
}

disease_symptom_profiles = {
    'flu': [
        [1,1,1,1,1,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,1,1,0,1,0,0,0,0,0,0,1,0]
    ],
    'cold': [
        [0,1,0,1,1,1,0,0,0,0,0,0,0,0,0],
        [0,1,0,0,1,1,0,0,0,0,0,0,0,0,0],
        [0,1,0,1,0,1,0,0,0,0,0,0,0,0,0]
    ],
    'malaria': [
        [1,0,1,1,0,0,1,1,1,1,0,0,0,1,1],
        [1,0,1,0,0,0,1,1,1,0,0,0,0,1,1],
        [1,0,1,1,0,0,1,0,1,1,0,0,0,0,1]
    ],
    'dengue': [
        [1,0,1,1,0,0,1,1,1,0,0,0,0,1,0],
        [1,0,1,0,0,0,1,1,0,0,0,0,0,1,0],
        [1,0,1,1,0,0,1,1,0,0,0,0,0,1,1]
    ],
    'covid-19': [
        [1,1,1,1,0,1,1,0,0,0,1,1,0,1,0],
        [1,1,1,1,0,1,1,0,0,0,1,0,0,1,0],
        [1,1,1,1,0,1,1,0,0,0,1,1,0,1,1]
    ]
}

def find_differentiating_symptoms(candidates, user_vector):
    combined_profiles = []
    for disease in candidates:
        profiles = np.array(disease_symptom_profiles[disease])
        combined = np.max(profiles, axis=0)
        combined_profiles.append(combined)
    combined_profiles = np.array(combined_profiles)

    differentiating = []
    for idx, symptom in enumerate(symptoms_list):
        vals = combined_profiles[:, idx]
        if np.any(vals == 1) and not np.all(vals == vals[0]):
            if user_vector[idx] == 0:
                differentiating.append(symptom)
    return differentiating

# Routes
@app.route('/')
def home():
    return render_template('indexx.html')

@app.route('/mainpage')
def mainpage():
    return render_template('mainpage.html')

@app.route('/indexx')
def indexx():
    return render_template('indexx.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    msg_type = data.get('type', '')

    if msg_type == 'diabetes':
        try:
            features = np.array([[
                float(data['Pregnancies']),
                float(data['Glucose']),
                float(data['BloodPressure']),
                float(data['SkinThickness']),
                float(data['Insulin']),
                float(data['BMI']),
                float(data['DiabetesPedigreeFunction']),
                float(data['Age'])
            ]])
            scaled = diabetes_scaler.transform(features)
            prediction = int(diabetes_model.predict(scaled)[0])
            message = "You likely have diabetes." if prediction == 1 else "You are likely not diabetic."
            return jsonify({'prediction': prediction, 'message': message})
        except Exception as e:
            return jsonify({'error': f'Error during diabetes prediction: {str(e)}'})

    # Default to illness prediction
    user_message = data.get('message', '').lower()
    user_vector = np.array([1 if symptom in user_message else 0 for symptom in symptoms_list])

    if hasattr(illness_model, "predict_proba"):
        probs = illness_model.predict_proba([user_vector])[0]
        classes = illness_model.classes_
        top_indices = probs.argsort()[-2:][::-1]
        top_diseases = [classes[i].lower() for i in top_indices]
        top_probs = probs[top_indices]
    else:
        top_disease = illness_model.predict([user_vector])[0].lower()
        top_diseases = [top_disease]
        top_probs = [1.0]

    if len(top_diseases) > 1 and abs(top_probs[0] - top_probs[1]) < 0.1:
        questions = find_differentiating_symptoms(top_diseases, user_vector)
        if questions:
            return jsonify({
                'follow_up': True,
                'questions': questions,
                'message': 'Your symptoms match multiple illnesses. Can you confirm if you have any of the following?'
            })

    prediction = top_diseases[0]
    precautions = precautions_dict.get(prediction, [])
    return jsonify({'prediction': prediction.capitalize(), 'precautions': '\n'.join(precautions)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
