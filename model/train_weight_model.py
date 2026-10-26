import pandas as pd
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "weight_data.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "weight_model.pkl"
)


data = pd.read_csv(DATASET_PATH)


activity_mapping = {
    "Low": 0,
    "Moderate": 1,
    "High": 2
}


if data["activity_level"].dtype == object:
    data["activity_level"] = data["activity_level"].map(
        activity_mapping
    )


features = [
    "age",
    "gender",
    "height",
    "current_weight",
    "exercise_minutes",
    "calories",
    "sleep_hours",
    "activity_level",
    "months"
]


target = "future_weight"


X = data[features]
y = data[target]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)


model.fit(X_train, y_train)


predictions = model.predict(X_test)


mae = mean_absolute_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)


print("Weight Prediction Model Training Completed!")
print("Mean Absolute Error:", round(mae, 2))
print("R2 Score:", round(r2, 2))


joblib.dump(
    model,
    MODEL_PATH
)


print("Weight model saved successfully!")
print("Model path:", MODEL_PATH)