import os
import joblib
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "weight_model.pkl"
)


model = joblib.load(MODEL_PATH)


def convert_activity_level(activity_level):

    activity_mapping = {
        "Low": 0,
        "Moderate": 1,
        "High": 2
    }

    return activity_mapping.get(
        activity_level,
        1
    )


def predict_weight(
    current_weight,
    height,
    age,
    gender,
    exercise_minutes,
    calories,
    sleep_hours,
    activity_level,
    months=5
):

    activity_level_value = convert_activity_level(
        activity_level
    )

    input_data = pd.DataFrame([{
        "age": age,
        "gender": int(gender),
        "height": height,
        "current_weight": current_weight,
        "exercise_minutes": exercise_minutes,
        "calories": calories,
        "sleep_hours": sleep_hours,
        "activity_level": activity_level_value,
        "months": months
    }])

    predicted_weight = model.predict(
        input_data
    )[0]

    if predicted_weight < 20:
        predicted_weight = 20

    return round(
        float(predicted_weight),
        2
    )


def predict_weight_progress(
    current_weight,
    height,
    age,
    gender,
    exercise_minutes,
    calories,
    sleep_hours,
    activity_level,
    months=5
):

    progress_weights = []

    for month in range(1, months + 1):

        predicted_weight = predict_weight(
            current_weight,
            height,
            age,
            gender,
            exercise_minutes,
            calories,
            sleep_hours,
            activity_level,
            months=month
        )

        progress_weights.append(
            predicted_weight
        )

    return [
        round(float(current_weight), 2)
    ] + progress_weights