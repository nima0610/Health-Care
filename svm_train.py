# svm_train.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import joblib
import os

# Load dataset from URL
url = "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv"
df = pd.read_csv(url)

# Keep only the required 8 features (already match your list)
features = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']
X = df[features]
y = df['Outcome']  # Target column

# Handle missing/zero values for some features (common in Pima dataset)
# Replace zeros with median in features where zero is invalid
for col in ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']:
    X[col] = X[col].replace(0, X[col].median())

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42)

# Train SVM model
model = SVC(kernel='linear')
model.fit(X_train, y_train)

# Feature importance from linear SVM weights
coef = model.coef_[0]
print("Feature weights (importance):")
for name, weight in zip(features, coef):
    print(f"{name}: {weight:.4f}")

# Save model and scaler
if not os.path.exists('model'):
    os.makedirs('model')

joblib.dump(model, 'model/diabetes_model.pkl')
joblib.dump(scaler, 'model/scaler.pkl')
