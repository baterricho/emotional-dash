from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <body style="background:black;color:white;text-align:center">
    <h1>Emotional Dash</h1>
    <p>Game server running</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)