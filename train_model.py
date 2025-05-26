import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
import pickle
import os

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Generate initial data covering all PHQ-9 score ranges
scores = list(range(0, 28))  # PHQ-9 scores range from 0 to 27
data = []

# Generate base samples
samples_per_score = 50  # We'll use fewer base samples since SMOTE will help balance
for score in scores:
    for _ in range(samples_per_score):
        data.append([float(score)])  # Use exact scores for initial data

X = np.array(data)

# Generate corresponding labels
def get_depression_level(score):
    if score <= 4:
        return 'Minimal or No Depression'
    elif score <= 9:
        return 'Mild Depression'
    elif score <= 14:
        return 'Moderate Depression'
    elif score <= 19:
        return 'Moderately Severe Depression'
    else:
        return 'Severe Depression'

y = np.array([get_depression_level(score[0]) for score in data])

# Split the data before applying SMOTE
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Scale the features before SMOTE
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Apply SMOTE to balance the classes
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

# Encode the labels after SMOTE
le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train_resampled)
y_test_encoded = le.transform(y_test)

# Print unique labels and their encodings
print("\nLabel Encodings:")
for i, label in enumerate(le.classes_):
    print(f"{label} -> {i}")

# Print class distribution after SMOTE
unique, counts = np.unique(y_train_resampled, return_counts=True)
print("\nClass distribution after SMOTE:")
for label, count in zip(unique, counts):
    print(f"{label}: {count}")

# Train the model with optimized parameters
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42
)
model.fit(X_train_resampled, y_train_encoded)

# Evaluate the model
y_pred = model.predict(X_test_scaled)
print("\nAccuracy:", accuracy_score(y_test_encoded, y_pred))
print("\nClassification Report:")
print(classification_report(y_test_encoded, y_pred, target_names=le.classes_))

# Test prediction for boundary cases and regular cases
print("\nTest Predictions:")
test_scores = [0, 2, 4, 5, 7, 9, 10, 12, 14, 15, 17, 19, 20, 22, 25]
for score in test_scores:
    scaled = scaler.transform([[score]])
    pred = model.predict(scaled)[0]
    label = le.inverse_transform([pred])[0]
    print(f"Score {score} -> {label}")

# Save the model, scaler, and label encoder in the models directory
print("\nSaving model files...")
with open('models/depression_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("Saved depression_model.pkl")

with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
print("Saved scaler.pkl")

with open('models/label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)
print("Saved label_encoder.pkl")

if __name__ == "__main__":
    train_model() 