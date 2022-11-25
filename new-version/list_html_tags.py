# %%
"""We need to convert the HTML tags to LaTeX instructions. I think it's best to
just make a long list of all the tags we can find in the articles, and then
manually convert them. (Or find something online). From that point onward, if we
can't recognize a tag we need to ignore it, but also somehow log this result."""

import json
import pathlib

files = list(pathlib.Path("json").glob("*.json"))
art_id = 18
print(files[art_id])

data = json.loads(files[art_id].read_text())
data.keys()

data["description"]
print(data.keys())
print(data["doi"])
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

    return result.rstrip()


def escape_ampersand(string):
    return string.replace("&", "\\&")


def _make_authors_text(authors):
    """Make string displaying author information"""
    out = ""
    out += "\n" + r"\vspace{-1ex}{by " + "\small"
    for i, author in enumerate(authors):
        out += r"\textbf{\textcolor{AuthorColor}{\small "
        out += author["name"]
        out += "}}"

        out += r"$^{"
        out += str(author["affiliation"])
        out += r"}$ "

        out += author["title"]

        if i != len(authors) - 1:
            out += r" $\mid$ "
        out += " "
    out += "}"
    return out


def _process_authors(authors):
    affiliations = {}
    author_dicts = []
    affil_counter = 1
    for author in authors:
        if author["research_institute"] not in affiliations:
            affiliations[author["research_institute"]] = affil_counter
            affil_counter += 1
        author_dicts.append(
            {
                "name": escape_ampersand(
                    author["first_name"] + " " + author["last_name"]
                ),
                "affiliation": affiliations[author["research_institute"]],
                "title": escape_ampersand(author["position"]),
            }
        )

    return author_dicts, affiliations


def _make_affiliations_text(affiliations):
    """Insert the affiliations into the main file"""
    out = ""
    out += "\n" + r"{\footnotesize "
    for affiliation, affil_id in affiliations.items():
        out += r"${}^" + str(affil_id) + r"$: " + affiliation + r"\\ "
    out += r"}"
    return out


def _get_img(data):
    image_name = pathlib.Path(data["image_path"]).name
    image_path = data["image_path"]
    if not image_path.startswith("http"):
        img_url = "https://thesciencebreaker.org/" + data["image_path"]
    else:
        img_url = image_path
    img_filename = pathlib.Path("tmp") / image_name

    import requests

    resp = requests.get(img_url)
    with open(img_filename, "wb") as f:
        f.write(resp.content)

    return image_name, resp.status_code


def process_data(data):
    template_data = {}

    template_data["mainText"] = html_to_latex(data["content"])
    template_data["subjectTitle"] = html_to_latex(data["title"])
    template_data["abstractText"] = html_to_latex(data["description"])
    published_time = datetime.strptime(
        data["published_at"], "%Y-%m-%d %H:%M:%S"
    )
    template_data["date"] = published_time.strftime("%B %d, %Y")
    template_data["subjectSelect"] = CAT_ID_TO_NAME[data["category_id"]]

    authors, affiliations = _process_authors(data["authors"])
    template_data["authorText"] = _make_authors_text(authors)
    template_data["affiliationText"] = _make_affiliations_text(affiliations)
    template_data["editorName"] = f"scientific editor \# {data['editor_id']}"

    template_data["fileName"], status_code = _get_img(data)
    if status_code != 200:
        print("ERROR downloading image, status code:", status_code)
        template_data["useImage"] = "\imagefalse"
    else:
        template_data["useImage"] = "\imagetrue"
    template_data["imageCredits"] = data["image_credits"]

    template_data["citation"] = html_to_latex(data["original_article"])
    return template_data


# template_data = process_data(data)
# %%
# %%
import jinja2
import os

latex_jinja_env = jinja2.Environment(
    block_start_string="\BLOCK{",
    block_end_string="}",
    variable_start_string="\VAR{",
    variable_end_string="}",
    comment_start_string="\#{",
    comment_end_string="}",
    line_statement_prefix="%%",
    line_comment_prefix="%#",
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(pathlib.Path(".").resolve()),
)

TEMPLATE_PATH = pathlib.Path("templates") / "template.tex"


def make_latex(template_data):
    tmp = pathlib.Path("tmp")
    main_file = tmp / "main.tex"
    template = latex_jinja_env.get_template(TEMPLATE_PATH.as_posix())

    with open(main_file, "w") as f:
        f.write(template.render(**template_data))


import subprocess


def make_pdf(data):
    tmp = pathlib.Path("tmp")
    template_data = process_data(data)
    make_latex(template_data)

    # Now we can compile the tex-file
    print("Compiling PDF...")
    tex_log = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
        capture_output=True,
        cwd=tmp,
    )
    num_errors = 0
    for line in tex_log.stdout.decode("utf-8").split("\n"):
        if line.startswith("!"):
            print("\n")
            print(line)
            print("\n")
            num_errors += 1
    if num_errors > 0:
        print("Some errors were encountered with latex. Entire log:")
        print(tex_log.stdout.decode("utf-8"))
    else:
        print("PDF compiled without errors!")


make_pdf(data)
# %%
