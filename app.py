from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

app.secret_key = "mysecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://finance_user:finance_pass@postgres:5432/finance_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# User Table
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# ======================
# Income Table
# ======================
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

# ======================
# Expense Table
# ======================
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

# ======================
# Home
# ======================
@app.route("/")
def home():
    return render_template("index.html")

# ======================
# Register
# ======================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        user = User(name=name, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# ======================
# Login
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session["user_name"] = user.name
            session["user_id"] = user.id
            return redirect("/dashboard")

        return "Invalid Email or Password"

    return render_template("login.html")

# ======================
# Dashboard
# ======================
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    total_income = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=user_id).scalar() or 0
    total_expense = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=user_id).scalar() or 0

    savings = total_income - total_expense

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        income=total_income,
        expense=total_expense,
        savings=savings
    )

# ======================
# Add Income
# ======================
@app.route("/add-income", methods=["GET", "POST"])
def add_income():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        amount = float(request.form["amount"])
        source = request.form["source"]

        income = Income(amount=amount, source=source, user_id=session["user_id"])
        db.session.add(income)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_income.html")

# ======================
# Add Expense
# ======================
@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        amount = float(request.form["amount"])
        category = request.form["category"]

        expense = Expense(amount=amount, category=category, user_id=session["user_id"])
        db.session.add(expense)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_expense.html")

# ======================
# History
# ======================
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    return render_template("history.html", incomes=incomes, expenses=expenses)

# ======================
# DELETE INCOME
# ======================
@app.route("/delete-income/<int:id>")
def delete_income(id):

    if "user_id" not in session:
        return redirect("/login")

    income = Income.query.get(id)

    if income and income.user_id == session["user_id"]:
        db.session.delete(income)
        db.session.commit()

    return redirect("/history")

# ======================
# DELETE EXPENSE
# ======================
@app.route("/delete-expense/<int:id>")
def delete_expense(id):

    if "user_id" not in session:
        return redirect("/login")

    expense = Expense.query.get(id)

    if expense and expense.user_id == session["user_id"]:
        db.session.delete(expense)
        db.session.commit()

    return redirect("/history")

# ======================
# 🔥 CHART ROUTE (NEW)
# ======================
@app.route("/chart")
def chart():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    total_income = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=user_id).scalar() or 0
    total_expense = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=user_id).scalar() or 0
    savings = total_income - total_expense

    labels = ["Income", "Expense", "Savings"]
    values = [total_income, total_expense, savings]

    plt.figure(figsize=(5,5))
    plt.pie(values, labels=labels, autopct='%1.1f%%')
    plt.title("Finance Overview")

    path = os.path.join("static", "chart.png")
    plt.savefig(path)
    plt.close()

    return render_template("chart.html")

# ======================
# Logout
# ======================
@app.route("/logout")
def logout():

    session.pop("user_name", None)
    session.pop("user_id", None)

    return redirect("/login")

# ======================
# Run App
# ======================
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)