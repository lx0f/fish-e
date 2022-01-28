from flask import Flask, render_template


app = Flask(__name__)

@app.route("/")
@app.route("/landing")
@app.route("/index")
def render_landing():
    return render_template("landing.html")


if __name__ == "__main__":
    app.run(debug=True)