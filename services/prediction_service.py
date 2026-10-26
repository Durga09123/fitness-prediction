import pickle

with open("model/fitness_model.pkl", "rb") as file:
    model = pickle.load(file)


def predict_fitness(
    age,
    gender,
    height,
    weight,
    exercise_minutes,
    calories,
    sleep_hours
):

    input_data = [[
        age,
        gender,
        height,
        weight,
        exercise_minutes,
        calories,
        sleep_hours
    ]]

    prediction = model.predict(input_data)

    return prediction[0]