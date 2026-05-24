from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-me-in-production"

messages = []


@app.route("/")
def home():
    return render_template("home.html", year=datetime.now().year)


@app.route("/about")
def about():
    return render_template("about.html", year=datetime.now().year)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("All fields are required.", "error")
        else:
            messages.append(
                {
                    "name": name,
                    "email": email,
                    "message": message,
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            )
            flash("Thanks for reaching out! We'll get back to you soon.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html", year=datetime.now().year)


@app.route("/messages")
def view_messages():
    return render_template("messages.html", messages=messages, year=datetime.now().year)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
