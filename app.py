from flask import Flask, render_template, request, jsonify, session, redirect
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Fix for no GUI / warning
import matplotlib.pyplot as plt

from io import BytesIO
import base64
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session management

# Load models
with open('svm_model.pkl', 'rb') as f:
    illness_model = pickle.load(f)

with open('diabetes_svm_model.pkl', 'rb') as f:
    diabetes_model = pickle.load(f)

with open('diabetes_scaler.pkl', 'rb') as f:
    diabetes_scaler = pickle.load(f)

symptoms_list = [
    'fever', 'headache', 'eye pain', 'cough', 'sneezing',
    'nasal congestion', 'sore throat', 'runny nose', 'fatigue',
    'body ache', 'joint pain', 'diarrhea', 'vomiting',
    'abdominal pain', 'nausea', 'rash', 'shortness of breath',
    'loss of taste and smell'
]

precautions_dict = {
    'diabetes': [
        'Maintain a balanced diet', 'Exercise regularly', 'Monitor blood sugar levels',
        'Take medication as prescribed', 'Avoid excessive sugar intake'
    ],
    'flu': [
        'Get plenty of rest', 'Drink fluids to stay hydrated',
        'Take antiviral medications if prescribed', 'Cover your mouth when coughing or sneezing',
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
    [1,1,0,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0],
    [1,0,0,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0],
    [1,1,0,1,1,1,1,0,0,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,1,1,1,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,0,1,1,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0],
    [1,1,0,1,1,0,1,0,1,1,1,0,0,0,0,0,0,0],
    [1,0,0,1,1,1,1,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,1,1,1,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,1,1,1,0,0,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,1,0,1,0,1,1,0,0,0,0,0,0,0,0],
    [1,1,0,1,0,1,1,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,0,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0]
    ],
    'cold': [
       [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0]
    ],
    'malaria': [
        [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0]
    ],
    'dengue': [
        [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0],
    [1,1,1,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0]
    ],
    'covid-19': [
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1],
    [1,1,0,1,0,0,1,0,1,1,0,0,0,0,0,0,1,1]
    ]
}

def find_differentiating_symptoms(candidates, user_vector, asked_symptoms=set()):
    candidate_profiles = [disease_symptom_profiles[d] for d in candidates]
    combined_profiles = []
    for disease in candidates:
        profiles = np.array(disease_symptom_profiles[disease])
        combined = np.max(profiles, axis=0)
        combined_profiles.append(combined)
    combined_profiles = np.array(combined_profiles)

    differentiating = []
    for idx, symptom in enumerate(symptoms_list):
        if symptom in asked_symptoms:
            continue  # Skip already asked symptoms
        vals = combined_profiles[:, idx]
        # Check if symptom distinguishes candidates and user doesn't have it yet
        if np.any(vals == 1) and not np.all(vals == vals[0]):
            if user_vector[idx] == 0:
                differentiating.append(symptom)
    return differentiating

def plot_svm_2d(X, y, user_point, symptom_names, class_names):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    svm = SVC(kernel='linear')
    svm.fit(X_scaled, y)

    user_scaled = scaler.transform([user_point])

    plt.figure(figsize=(6,5))
    colors = ['red' if label == 0 else 'blue' for label in y]
    labels_map = {0: class_names[0], 1: class_names[1]}
    for class_value in [0, 1]:
        plt.scatter(
            X_scaled[np.array(y) == class_value, 0],
            X_scaled[np.array(y) == class_value, 1],
            label=labels_map[class_value],
            s=100,
            edgecolors='k',
            alpha=0.7
        )
    plt.scatter(user_scaled[0, 0], user_scaled[0, 1], color='green', s=150, marker='*', label='Your Symptoms')

    ax = plt.gca()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    xx = np.linspace(xlim[0], xlim[1], 50)
    yy = np.linspace(ylim[0], ylim[1], 50)
    YY, XX = np.meshgrid(yy, xx)
    xy = np.vstack([XX.ravel(), YY.ravel()]).T
    Z = svm.decision_function(xy).reshape(XX.shape)

    ax.contour(XX, YY, Z, colors='k', levels=[0], alpha=0.8, linestyles=['-'])
    ax.contour(XX, YY, Z, colors='k', levels=[-1, 1], alpha=0.3, linestyles=['--'])

    plt.xlabel(symptom_names[0])
    plt.ylabel(symptom_names[1])
    plt.title(f"SVM Hyperplane: {class_names[0]} vs {class_names[1]}")
    plt.legend()
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

@app.route('/')
def home():
    return render_template('indexx.html')

@app.route('/mainpage')
def mainpage():
    return render_template('mainpage.html')

@app.route('/indexx')
def indexx():
    return render_template('indexx.html')

@app.route('/login')
def login():
    return redirect("http://localhost:5002/")

@app.route('/index')
def index():
    return redirect("http://localhost:5001/")

@app.route('/consult')
def consult():
    return redirect("http://localhost:5005/")


@app.route('/reset')
def reset():
    session.clear()
    return jsonify({'message': 'Session cleared.'})


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    msg_type = data.get('type', '')
    user_message = data.get('message', '').lower()

    if 'start over' in user_message:
        session.clear()
        return jsonify({'prediction': "Let's start fresh. Please tell me your symptoms.", 'precautions': ''})

    session_symptoms = session.get('symptoms', [0]*len(symptoms_list))
    asked_symptoms = set(session.get('asked', []))

    new_symptoms = [1 if symptom in user_message else 0 for symptom in symptoms_list]
    user_vector = np.array([max(session_symptoms[i], new_symptoms[i]) for i in range(len(symptoms_list))])
    session['symptoms'] = user_vector.tolist()

    # Diabetes prediction
    if msg_type == 'diabetes':
        try:
            features = [
                float(data['Pregnancies']), float(data['Glucose']),
                float(data['BloodPressure']), float(data['SkinThickness']),
                float(data['Insulin']), float(data['BMI']),
                float(data['DiabetesPedigreeFunction']), float(data['Age'])
            ]
            scaled = diabetes_scaler.transform([features])
            prediction_num = diabetes_model.predict(scaled)[0]
            prediction = 'Diabetic' if prediction_num == 1 else 'Not Diabetic'
            precautions = precautions_dict.get('diabetes', [])
            return jsonify({'prediction': prediction, 'precautions': '\n'.join(precautions)})
        except Exception:
            return jsonify({'error': 'Error during diabetes prediction.'})

    greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'hey there']
    is_greeting = any(greet in user_message for greet in greetings)
    has_symptom = np.any(user_vector)

    if not is_greeting and not has_symptom:
        return jsonify({'prediction': "Couldn't understand your message.", 'precautions': ''})
    if not has_symptom and is_greeting:
        return jsonify({'prediction': "Hello! Please tell me your symptoms so I can help you.", 'precautions': ''})

    if hasattr(illness_model, "predict_proba"):
        probs = illness_model.predict_proba([user_vector])[0]
        classes = illness_model.classes_
        top_indices = probs.argsort()[-2:][::-1]
        top_diseases = [classes[i].lower() for i in top_indices]
        top_probs = [round(probs[i] * 100, 1) for i in top_indices]
    else:
        top_disease = illness_model.predict([user_vector])[0].lower()
        top_diseases = [top_disease]
        top_probs = [100.0]

    # Follow-up logic
    if len(top_diseases) > 1 and abs(top_probs[0] - top_probs[1]) < 10:
        questions = find_differentiating_symptoms(top_diseases, user_vector, asked_symptoms)
        if questions:
            asked_symptoms.update(questions)
            session['asked'] = list(asked_symptoms)

            return jsonify({
                'follow_up': True,
                'questions': questions,
                'message': 'Your symptoms match multiple illnesses. Can you please specify if you have any of the following symptoms?'
            })

    prediction_text = ', '.join([f"{name.capitalize()} ({p}%)" for name, p in zip(top_diseases, top_probs)])
    precautions = precautions_dict.get(top_diseases[0], [])

    # SVM plot
    plot_img_base64 = None
    if len(top_diseases) >= 2:
        d1, d2 = top_diseases[0], top_diseases[1]
        profiles1 = np.array(disease_symptom_profiles.get(d1, []))
        profiles2 = np.array(disease_symptom_profiles.get(d2, []))

        if profiles1.size and profiles2.size:
            class_names = [d1.capitalize(), d2.capitalize()]
            X = []
            y = []

            for profile in profiles1:
                X.append(profile[[symptoms_list.index('fever'), symptoms_list.index('headache')]])
                y.append(0)
            for profile in profiles2:
                X.append(profile[[symptoms_list.index('fever'), symptoms_list.index('headache')]])
                y.append(1)

            user_point = user_vector[[symptoms_list.index('fever'), symptoms_list.index('headache')]]
            plot_img_base64 = plot_svm_2d(np.array(X), np.array(y), user_point, ['fever', 'headache'], class_names)

    # Final response
    response = jsonify({
        'prediction': prediction_text,
        'precautions': '\n'.join(precautions),
        'plot': plot_img_base64,
        'follow_up': False
    })

    session.clear()  # ✅ Clear session after complete prediction
    return response


if __name__ == '__main__':
    app.run(debug=True)