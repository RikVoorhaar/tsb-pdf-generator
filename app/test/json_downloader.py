# %%
import requests
import json
from tqdm import tqdm
from pathlib import Path
import logging
import dotenv
import os

dotenv.load_dotenv()
LOG_FILE = Path("json_downloader.log")
logging.basicConfig(
    level=logging.DEBUG,
    filename=LOG_FILE,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("info: Starting json_downloader.py")

for art_id in tqdm(range(36, 4000)):
    file_name = f"break_{art_id}.json"
    file_loc = Path("json") / file_name
    if file_loc.exists():
        continue
    resp = requests.get(
        f"https://thesciencebreaker.org/json/{art_id}?id={os.environ['TSB_ID']}"
    )

    try:
        resp_json = resp.json()
        logger.info(f"Downloaded {file_name}")
    except json.JSONDecodeError:
        logger.error(f"Error with {art_id}")
        continue

    if len(resp_json) > 0:
        with open(file_loc, "w") as f:
            json.dump(resp_json, f)
    else:
        print(f"{art_id} was empty")

# %%
