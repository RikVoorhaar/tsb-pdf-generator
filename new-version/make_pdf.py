# %%
"""We need to convert the HTML tags to LaTeX instructions. I think it's best to
just make a long list of all the tags we can find in the articles, and then
manually convert them. (Or find something online). From that point onward, if we
can't recognize a tag we need to ignore it, but also somehow log this result."""

import subprocess
from datetime import datetime
from pathlib import Path
import logging

import jinja2
import pandoc
import requests

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

TEMPLATE_PATH = Path("templates") / "template.tex"

LATEX_JINJA_ENV = jinja2.Environment(
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
    loader=jinja2.FileSystemLoader(Path(".").resolve()),
)


def html_to_latex(html_text):
    if html_text is None:
        return ""
    Path("tmp").mkdir(exist_ok=True)

    doc = pandoc.read(html_text, format="html")
    result = pandoc.write(doc, "tmp/html_text.tex", format="latex")

    Path("tmp/html_text.tex").unlink()

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
                "name": (author["first_name"] + " " + author["last_name"]),
                "affiliation": affiliations[author["research_institute"]],
                "title": (author["position"]),
            }
        )

    return author_dicts, affiliations


def _make_affiliations_text(affiliations):
    """Insert the affiliations into the main file"""
    out = ""
    out += "\n" + r"{"
    for affiliation, affil_id in affiliations.items():
        out += r"${}^" + str(affil_id) + r"$: " + affiliation + r"\\ "
    out += r"}"
    return out


def _get_img(data):
    image_name = Path(data["image_path"]).name
    image_path = data["image_path"]
    if not image_path.startswith("http"):
        img_url = "https://thesciencebreaker.org/" + data["image_path"]
    else:
        img_url = image_path
    img_filename = Path("tmp") / image_name
    if img_filename.exists():
        logging.info("Image already downloaded, skipping")
        return image_name, 200

    logging.info("Downloading image %s", img_url)
    resp = requests.get(img_url)
    logging.info("Status code: %s", resp.status_code)
    if resp.status_code == 200:
        with open(img_filename, "wb") as f:
            f.write(resp.content)

    return image_name, resp.status_code


def process_data(data):
    template_data = {}

    template_data["mainText"] = html_to_latex(data["content"])
    template_data["subjectTitle"] = html_to_latex(data["title"])
    template_data["abstractText"] = html_to_latex(data["description"])
    if len(template_data["abstractText"]) > 0:
        template_data["useAbstract"] = r"\abstracttrue"
    else:
        template_data["useAbstract"] = r"\abstractfalse"
    published_time = datetime.strptime(
        data["published_at"], "%Y-%m-%d %H:%M:%S"
    )
    template_data["date"] = published_time.strftime("%B %d, %Y")
    template_data["subjectSelect"] = CAT_ID_TO_NAME[data["category_id"]]

    authors, affiliations = _process_authors(data["authors"])
    template_data["authorText"] = escape_ampersand(_make_authors_text(authors))
    template_data["affiliationText"] = escape_ampersand(_make_affiliations_text(affiliations))
    template_data["editorName"] = f"scientific editor \# {data['editor_id']}"

    template_data["fileName"], status_code = _get_img(data)
    if status_code != 200:
        template_data["useImage"] = "\imagefalse"
    else:
        template_data["useImage"] = "\imagetrue"
    template_data["imageCredits"] = data["image_credits"]

    template_data["citation"] = html_to_latex(data["original_article"])
    return template_data


def make_latex(template_data):
    tmp = Path("tmp")
    main_file = tmp / "main.tex"
    template = LATEX_JINJA_ENV.get_template(TEMPLATE_PATH.as_posix())

    with open(main_file, "w") as f:
        f.write(template.render(**template_data))


def make_pdf(data):
    tmp = Path("tmp")
    logging.info("processing data")
    template_data = process_data(data)
    logging.info("making LaTeX")
    make_latex(template_data)

    # Now we can compile the tex-file
    logging.info("Compiling PDF...")
    tex_log = subprocess.run(
        # ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
        ["xelatex", "-interaction=nonstopmode", "main.tex"],
        capture_output=True,
        cwd=tmp,
    )
    num_errors = 0
    for line in tex_log.stdout.decode("utf-8").split("\n"):
        if line.startswith("!"):
            logging.log(logging.ERROR, line)
            num_errors += 1
    logging.info("Done compiling PDF, %d errors", num_errors)
    return 0 if num_errors == 0 else 1


# %%
