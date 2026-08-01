from flask import Flask, render_template

from backend.auth import auth

app = Flask(__name__)

# Register Blueprint
app.register_blueprint(auth)


@app.route("/dashboard")
def dashboard():
    return render_template("dash.html")


if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True)