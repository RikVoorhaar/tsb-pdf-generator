# %%
import requests
import json
from tqdm import tqdm

for art_id in tqdm(range(36,400)):
    resp = requests.get(f"https://thesciencebreaker.org/json/{art_id}?id=$2y$10$P75HCBUqXIO65SvfjKQ4vOg0vCzAiTAmWrZ2YtGhGMTIafOsfIo4e")

    try:
        resp_json = resp.json()
    except json.JSONDecodeError:
        print(f"Error with {art_id}")
        continue

    if len(resp_json) > 0:
        with open(f"json/break_{art_id}.json", "w") as f:
            json.dump(resp_json, f)
    else:
        print(f"{art_id} was empty")
