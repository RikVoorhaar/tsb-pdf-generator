import os
import datetime
import json

from flask import Flask, flash, render_template, request
from werkzeug.utils import secure_filename

from make_pdf import make_pdf

try:
    os.mkdir("tmp")
except FileExistsError:
    pass
app = Flask(__name__)
app.secret_key = "secret key"
UPLOAD_FOLDER = "tmp"
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

SUBJECTS = (
    "Earth & Space",
    "Evolution & Behaviour",
    "Health & Physiology",
    "Maths, Physics & Chemistry",
    "Microbiology",
    "Neurobiology",
    "Plant Biology",
    "Psychology",
)


@app.route("/", methods=["GET", "POST"])
def index():
    vars = dict()
    num_affiliations = 5
    num_authors = 3
    vars["affiliation_ids"] = [str(i) for i in range(1, num_affiliations + 1)]
    vars["author_ids"] = [str(i) for i in range(1, num_authors + 1)]
    vars["subjects"] = SUBJECTS
    today = datetime.date.today()
    vars["today"] = today.strftime("%B %d, %Y")
    error_message = ""
    if request.method == "POST":
        # Handle the cover image upload
        file = request.files["coverImage"]
        if file.filename != "":
            filename = secure_filename(file.filename)
        elif request.form["fileName"] != "":
            filename = request.form["fileName"]
        else:
            filename = ""
            error_message+="No cover image selected\n"
        vars["fileName"] = filename

        filetype = filename.split(".")[-1]
        if filename != "" and filetype not in ["jpg", "png", "jpeg"]:
            error_message = "Invalid file type"
        elif file.filename != "":
            file.save(os.path.join("tmp", filename))

        # Check if subject has been selected
        if request.form["subjectSelect"] == "Choose subject...":
            error_message+="Please select a subject\n"

        # Check length of abstract
        abstract = request.form["abstractText"]
        if len(abstract) > 400:
            error_message+="Abstract is too long\n"

        if error_message == "":
            with open(os.path.join("tmp", "metadata.json"), "w") as f:
                metadata = request.form.to_dict()
                metadata["fileName"] = filename
                json.dump(metadata, f, indent=2)

        if error_message == "":
            make_pdf()

    if error_message != "":
        vars["error_message"] = error_message

    return render_template("index.html", **vars)
