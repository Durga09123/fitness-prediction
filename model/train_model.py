import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


# Load dataset
data = pd.read_csv("dataset/fitness_data.csv")


# Input features
X = data[
    [
        "age",
        "gender",
        "height",
        "weight",
        "exercise_minutes",
        "calories",
        "sleep_hours"
    ]
]


# Target
y = data["fitness_level"]


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Create model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


# Train model
model.fit(X_train, y_train)


# Test model
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)


# Save model
with open("model/fitness_model.pkl", "wb") as file:
    pickle.dump(model, file)


print("Model saved successfully!")