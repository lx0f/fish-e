# TODO : create login logic
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap5(app)
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profile_image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    # items = db.relationship("Item", backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}','{self.email}','{self.profile_image_file}')"


# NOTE : see issue #25
# class Item(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("user.id", nullable=False))
#     name = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     base_price = db.Column(db.Float)


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
    search = StringField(
        validators=[DataRequired()], render_kw={"placeholder": "Enter Search"}
    )
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
