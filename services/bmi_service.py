def calculate_bmi(weight, height):
    height_m = height / 100
    bmi = weight / (height_m * height_m)
    return round(bmi, 2)


def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"