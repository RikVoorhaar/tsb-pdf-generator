from pathlib import Path

from flask import Flask, send_file, request
from flask_api import status
from make_pdf import make_pdf

app = Flask(__name__)


@app.route("/", methods=["POST"])
def post_form():
    data = request.json
    pdf_location = make_pdf(data)
    return pdf_location, status.HTTP_201_CREATED


@app.route("/pdf/<filename>", methods=["GET"])
def get_pdf(filename):
    pdf_folder = Path("pdf")
    return send_file(pdf_folder / filename, as_attachment=True)
