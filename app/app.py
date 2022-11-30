from pathlib import Path
import re
import logging
import pandoc
import os
import json
import hashlib

from flask import Flask, send_file, request, session, redirect, url_for
from flask_api import status
import flask_login
from make_pdf import make_pdf

os.environ["NO_COLOR"] = "true"

app = Flask(__name__)
app.config.update(
    SERVER_NAME="tsb.rikvoorhaar.com",
    SECRET_KEY=os.environ["FLASK_SECRET_KEY"],
)


with open("users.json") as f:
    users = json.loads(f.read())
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

LOG_FOLDER = Path("logs")
LOG_FOLDER.mkdir(exist_ok=True)
LOG_FILE = LOG_FOLDER / "pdf_generator.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@app.route("/", methods=["POST", "GET"])
def post_form():
    if request.method == "POST":
        data = request.json
        pdf_location = make_pdf(data)
        return pdf_location, status.HTTP_201_CREATED
    elif request.method == "GET":
        return "The pdf generator is running", status.HTTP_200_OK


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get("email")
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
                <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
                </form>
                """

    email = request.form["email"]
    hasher = hashlib.sha256()
    hasher.update(request.form["password"].encode("ascii"))
    pass_sha = hasher.hexdigest()
    if email in users and pass_sha == users[email]:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect(url_for("protected"))

    return "Bad login"


@app.route("/protected")
@flask_login.login_required
def protected():
    return (
        "Logged in as: "
        + flask_login.current_user.id
        + "\n You can now access the logs"
    )


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return "Logged out"


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))


@app.route("/pdf/<filename>", methods=["GET"])
def get_pdf(filename):
    pdf_folder = Path("pdf")
    return send_file(pdf_folder / filename, as_attachment=True)


@app.route("/log", methods=["GET"])
@flask_login.login_required
def get_log():

    log_file = Path("logs") / "pdf_generator.log"
    with open(log_file, "r") as f:
        log = f.read()
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    log = ansi_escape.sub("", log)
    log = "```\n" + log + "\n```"
    doc = pandoc.read(log, format="markdown")
    result = pandoc.write(doc, "/tmp/tsb_pdf_generator_log.html", format="html")

    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
