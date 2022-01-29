# TODO : create login logic
from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

SECRET_KEY = "secret_key"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
Bootstrap5(app)

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 150)])
    remember = BooleanField("Remember me")
    submit = SubmitField()

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

if __name__ == "__main__":
    app.run(debug=True)
