document.addEventListener("DOMContentLoaded", function () {

    console.log("Fitness App JavaScript Loaded");

    const form = document.querySelector("form");

    if (form) {
        form.addEventListener("submit", function (event) {

            const exercise = document.querySelector(
                'input[name="exercise_minutes"]'
            );

            const sleep = document.querySelector(
                'input[name="sleep_hours"]'
            );

            if (exercise && exercise.value < 0) {
                alert("Exercise minutes cannot be negative.");
                event.preventDefault();
            }

            if (sleep && sleep.value < 1) {
                alert("Please enter valid sleep hours.");
                event.preventDefault();
            }

        });
    }

});