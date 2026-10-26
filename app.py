from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os

from werkzeug.security import generate_password_hash, check_password_hash

from services.bmi_service import calculate_bmi, get_bmi_category
from services.prediction_service import predict_fitness
from services.weight_prediction_service import predict_weight, predict_weight_progress


app = Flask(__name__)

app.secret_key = "fitness_prediction_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database", "fitness.db")


def init_db():

    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender INTEGER,
            height REAL,
            weight REAL,
            exercise_minutes INTEGER,
            calories INTEGER,
            sleep_hours REAL,
            bmi REAL,
            bmi_category TEXT,
            fitness_level TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(predictions)")

    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    if "user_id" not in column_names:

        cursor.execute("""
            ALTER TABLE predictions
            ADD COLUMN user_id INTEGER
        """)

    conn.commit()
    conn.close()


def login_required():

    if "user_id" not in session:
        return False

    return True


def get_dashboard_data():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    user_id = session.get("user_id")

    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE user_id = ?
    """, (user_id,))

    total_records = cursor.fetchone()[0]

    cursor.execute("""
        SELECT bmi, bmi_category, fitness_level, weight
        FROM predictions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    latest_record = cursor.fetchone()

    cursor.execute("""
        SELECT id, weight, bmi
        FROM predictions
        WHERE user_id = ?
        ORDER BY id ASC
    """, (user_id,))

    progress_records = cursor.fetchall()

    conn.close()

    if latest_record:

        latest_bmi = latest_record[0]
        bmi_category = latest_record[1]
        fitness_level = latest_record[2]
        latest_weight = latest_record[3]

    else:

        latest_bmi = None
        bmi_category = None
        fitness_level = None
        latest_weight = None

    progress_labels = []
    progress_weights = []
    progress_bmis = []

    for record in progress_records:

        progress_labels.append("Record " + str(record[0]))
        progress_weights.append(record[1])
        progress_bmis.append(record[2])

    return (
        total_records,
        latest_bmi,
        bmi_category,
        fitness_level,
        latest_weight,
        progress_labels,
        progress_weights,
        progress_bmis
    )


@app.route("/")
def home():

    if not login_required():
        return redirect(url_for("login"))

    (
        total_records,
        latest_bmi,
        bmi_category,
        fitness_level,
        latest_weight,
        progress_labels,
        progress_weights,
        progress_bmis
    ) = get_dashboard_data()

    return render_template(
        "dashboard.html",
        total_records=total_records,
        latest_bmi=latest_bmi,
        bmi_category=bmi_category,
        fitness_level=fitness_level,
        latest_weight=latest_weight,
        progress_labels=progress_labels,
        progress_weights=progress_weights,
        progress_bmis=progress_bmis,
        username=session.get("username")
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if username == "":
            return render_template(
                "register.html",
                error="Please enter username."
            )

        if email == "":
            return render_template(
                "register.html",
                error="Please enter email."
            )

        if password == "":
            return render_template(
                "register.html",
                error="Please enter password."
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        """, (
            username,
            email,
            hashed_password
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "login",
                registered="success"
            )
        )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    registered = request.args.get("registered")

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, password
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        conn.close()

        if user is None:

            return render_template(
                "login.html",
                error="Invalid email or password.",
                registered=registered
            )

        user_id = user[0]
        username = user[1]
        hashed_password = user[2]

        if not check_password_hash(
            hashed_password,
            password
        ):

            return render_template(
                "login.html",
                error="Invalid email or password.",
                registered=registered
            )

        session["user_id"] = user_id
        session["username"] = username
        session["email"] = email

        return redirect(url_for("home"))

    return render_template(
        "login.html",
        registered=registered
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/input")
def input_page():

    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "input.html",
        form_data={}
    )


@app.route("/predict", methods=["POST"])
def predict():

    if not login_required():
        return redirect(url_for("login"))

    age = int(request.form["age"])

    gender = request.form.get("gender", "")

    if gender == "":
        return render_template(
            "input.html",
            error="Please select your gender.",
            form_data=request.form
        )

    gender = int(gender)

    height = float(request.form["height"])
    weight = float(request.form["weight"])

    exercise_minutes = int(
        request.form["exercise_minutes"]
    )

    calories = int(
        request.form["calories"]
    )

    sleep_hours = float(
        request.form["sleep_hours"]
    )

    if age < 10 or age > 100:
        return render_template(
            "input.html",
            error="Please enter a valid age.",
            form_data=request.form
        )

    if height < 100 or height > 250:
        return render_template(
            "input.html",
            error="Please enter a valid height.",
            form_data=request.form
        )

    if weight < 20 or weight > 300:
        return render_template(
            "input.html",
            error="Please enter a valid weight.",
            form_data=request.form
        )

    if exercise_minutes < 0 or exercise_minutes > 600:
        return render_template(
            "input.html",
            error="Please enter valid exercise minutes.",
            form_data=request.form
        )

    if calories < 500 or calories > 10000:
        return render_template(
            "input.html",
            error="Please enter valid daily calories.",
            form_data=request.form
        )

    if sleep_hours < 1 or sleep_hours > 24:
        return render_template(
            "input.html",
            error="Please enter valid sleep hours.",
            form_data=request.form
        )

    bmi = calculate_bmi(weight, height)

    bmi_category = get_bmi_category(bmi)

    fitness_level = predict_fitness(
        age,
        gender,
        height,
        weight,
        exercise_minutes,
        calories,
        sleep_hours
    )

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions (
            user_id,
            age,
            gender,
            height,
            weight,
            exercise_minutes,
            calories,
            sleep_hours,
            bmi,
            bmi_category,
            fitness_level
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        age,
        gender,
        height,
        weight,
        exercise_minutes,
        calories,
        sleep_hours,
        bmi,
        bmi_category,
        fitness_level
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        bmi=bmi,
        bmi_category=bmi_category,
        fitness_level=fitness_level
    )


@app.route("/history")
def history():

    if not login_required():
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM predictions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
    ))

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )


@app.route("/delete-history", methods=["POST"])
def delete_history():

    if not login_required():
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM predictions
        WHERE user_id = ?
    """, (
        session["user_id"],
    ))

    conn.commit()
    conn.close()

    return render_template(
        "history.html",
        records=[]
    )


@app.route("/weight-prediction")
def weight_prediction_page():

    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "weight_input.html"
    )


@app.route("/predict-weight", methods=["POST"])
def predict_weight_page():

    if not login_required():
        return redirect(url_for("login"))

    weight = float(request.form["weight"])
    height = float(request.form["height"])
    age = int(request.form["age"])

    gender = request.form.get("gender", "")

    exercise_minutes = int(
        request.form["exercise_minutes"]
    )

    calories = int(
        request.form["calories"]
    )

    sleep_hours = float(
        request.form["sleep_hours"]
    )

    activity_level = request.form.get(
        "activity_level",
        ""
    )

    months = int(request.form["months"])

    if weight < 20 or weight > 300:
        return render_template(
            "weight_input.html",
            error="Please enter a valid weight."
        )

    if height < 100 or height > 250:
        return render_template(
            "weight_input.html",
            error="Please enter a valid height."
        )

    if age < 10 or age > 100:
        return render_template(
            "weight_input.html",
            error="Please enter a valid age."
        )

    if gender == "":
        return render_template(
            "weight_input.html",
            error="Please select your gender."
        )

    if exercise_minutes < 0 or exercise_minutes > 600:
        return render_template(
            "weight_input.html",
            error="Please enter valid exercise minutes."
        )

    if calories < 500 or calories > 10000:
        return render_template(
            "weight_input.html",
            error="Please enter valid daily calories."
        )

    if sleep_hours < 1 or sleep_hours > 24:
        return render_template(
            "weight_input.html",
            error="Please enter valid sleep hours."
        )

    if activity_level == "":
        return render_template(
            "weight_input.html",
            error="Please select your activity level."
        )

    if months < 1 or months > 12:
        return render_template(
            "weight_input.html",
            error="Please select a prediction period between 1 and 12 months."
        )

    predicted_weight = predict_weight(
        weight,
        height,
        age,
        gender,
        exercise_minutes,
        calories,
        sleep_hours,
        activity_level,
        months=months
    )

    progress_weights = predict_weight_progress(
        weight,
        height,
        age,
        gender,
        exercise_minutes,
        calories,
        sleep_hours,
        activity_level,
        months=months
    )

    progress_labels = ["Current"]

    for month in range(1, months + 1):

        progress_labels.append(
            "Month " + str(month)
        )

    weight_change = round(
        predicted_weight - weight,
        2
    )

    if weight_change < 0:
        prediction_type = "Weight Loss"

    elif weight_change > 0:
        prediction_type = "Weight Gain"

    else:
        prediction_type = "Weight Maintain"

    return render_template(
        "weight_result.html",
        current_weight=weight,
        predicted_weight=predicted_weight,
        weight_change=weight_change,
        prediction_type=prediction_type,
        progress_weights=progress_weights,
        progress_labels=progress_labels,
        months=months
    )


@app.route("/dashboard")
def dashboard():

    return home()


if __name__ == "__main__":

    init_db()

    app.run(debug=True)