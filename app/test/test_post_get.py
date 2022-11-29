# %%
import json
import requests
from pathlib import Path

files = list(Path("json").glob("*.json"))
json_file = Path("json") / "break_720.json"
data = json.loads(json_file.read_text())

# %%
url = "http://localhost:5000/"
resp_post = requests.post(url, json=data)
# %%
pdf_filename = resp_post.text
print(pdf_filename)
resp_get = requests.get(url + pdf_filename)
# %%
len(resp_get.content)
