# %%
"""We need to convert the HTML tags to LaTeX instructions. I think it's best to
just make a long list of all the tags we can find in the articles, and then
manually convert them. (Or find something online). From that point onward, if we
can't recognize a tag we need to ignore it, but also somehow log this result."""

import json
import pathlib

files = list(pathlib.Path("json").glob("*.json"))
art_id = 6
print(files[art_id])

data = json.loads(files[art_id].read_text())
data.keys()

data["description"]
print(data.keys())
from datetime import datetime

CAT_ID_TO_NAME = {
    1: "Health \& Physiology",
    2: "Neurobiology",
    3: "Earth \& Space",
    4: "Evolution \& Behaviour",
    5: "Plant Biology",
    6: "Microbiology",
    7: "Maths, Physics \& Chemistry",
    13: "Psychology",
}
# %%
import pandoc


def html_to_latex(html_text):
    if html_text is None:
        return ""
    pathlib.Path("tmp").mkdir(exist_ok=True)

    doc = pandoc.read(html_text, format="html")
    result = pandoc.write(doc, "tmp/html_text.tex", format="latex")

    pathlib.Path("tmp/html_text.tex").unlink()

    return result


def process_data(data):
    template_data = {}

    template_data["mainText"] = html_to_latex(data["content"])
    template_data["subjectTitle"] = html_to_latex(data["title"])
    template_data["abstract"] = html_to_latex(data["description"])
    published_time = datetime.strptime(
        data["published_at"], "%Y-%m-%d %H:%M:%S"
    )
    template_data["date"] = published_time.strftime("%B %d, %Y")
    template_data["subjectSelect"] = CAT_ID_TO_NAME[data["category_id"]]

    return template_data


template_data = process_data(data)
template_data["abstract"], data["description"]
# %%
"""content to fill out:
[x] date
[x] subjectSelect
[x] subjectTitle
[ ] authorText
[ ] affiliationText
[ ] editorName
[x] abstractText
[ ] fileName (the cover image)
[ ] imageCredits
[x] mainText
"""
