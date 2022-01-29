# TODO : create login logic
from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length

SECRET_KEY = "secret_key"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
Bootstrap5(app)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 150)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 150)])
    submit = SubmitField("Register")


class ForgetForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    submit = SubmitField("Submit")


class SearchForm(FlaskForm):
    search = StringField(validators=[DataRequired()], render_kw={"placeholder":"Enter Search"})
    submit = SubmitField("Search")

@app.route("/")
def render_landing():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def render_login():
    if request.method == "GET":
        return render_template("login.html", form=LoginForm())
    elif request.method == "POST":
        data = request.form
        return jsonify(data)


@app.route("/register", methods=["GET", "POST"])
def render_register():
    if request.method == "GET":
        return render_template("register.html", form=RegisterForm())
    elif request.method == "POST":
        data = request.form
        return jsonify(data)


@app.route("/forget", methods=["GET", "POST"])
def render_forget():
    if request.method == "GET":
        return render_template("forget.html", form=ForgetForm())
    elif request.method == "POST":
        data = request.form
        return jsonify(data)


@app.route("/home")
def render_home():
    return render_template("home.html", form=SearchForm())


if __name__ == "__main__":
    app.run(debug=True)
