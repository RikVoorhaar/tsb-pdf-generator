# %%
import json
import requests
from pathlib import Path

files = list(Path("json").glob("*.json"))

json_file = Path("json") / "break_274.json"
data = json.loads(json_file.read_text())

# %%
url = "http://tsb.rikvoorhaar.com/"
# url = "http://127.0.0.1:5000/"
response = requests.post(url, json=data)

pdf_filename = response.text
reponse = requests.get(url + pdf_filename)
print(pdf_filename)
# %%
with open(pdf_filename, "wb") as f:
    f.write(reponse.content)

# %%
