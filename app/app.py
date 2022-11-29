from pathlib import Path
import logging

from flask import Flask, send_file, request
from flask_api import status
from make_pdf import make_pdf


app = Flask(__name__)

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


@app.route("/pdf/<filename>", methods=["GET"])
def get_pdf(filename):
    pdf_folder = Path("pdf")
    return send_file(pdf_folder / filename, as_attachment=True)


@app.route("/log", methods=["GET"])
def get_log():
    log_folder = Path("logs")
    return send_file(log_folder / "pdf_generator.log")