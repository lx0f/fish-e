from flask import Flask, render_template
from flask_bootstrap import Bootstrap5


app = Flask(__name__)
Bootstrap5(app)

@app.route("/")
def render_landing():
    return render_template("index.html")

@app.route("/login")
def render_login():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)