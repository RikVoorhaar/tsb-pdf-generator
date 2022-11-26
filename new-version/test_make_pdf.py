# %%
"""
We run the make_pdf routine for all the jsons. They should all compile without errors.
"""
import json
import logging
from pathlib import Path

from tqdm import tqdm

from make_pdf import make_pdf

LOG_FILE = Path("tmp/test_make_pdf.log")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


logger.info("info: Starting test_make_pdf.py")

# %%
files = list(Path("json").glob("*.json"))


def test_json(data):
    logger.info("\n" + "-" * 80)
    logger.info(f"Testing {data['id']}")
    logger.info(f"Doi: {data['doi']}")

    try:
        latex_errors = make_pdf(data)
    except Exception as e:
        logging.error(f"Error: {e}")
        raise


# %%
json_file = Path("json") / "break_70.json"
data = json.loads(json_file.read_text())
test_json(data)
# %%
for f in tqdm(files):
    data = json.loads(f.read_text())
    test_json(data)

# %%
# %%
