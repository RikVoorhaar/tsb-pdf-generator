import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import jinja2
import pandoc
import requests

# Map category ID to correct names
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
    """Convert HTML to LaTeX using pandoc"""
    if html_text is None:
        return ""
    Path("tmp").mkdir(exist_ok=True)

    doc = pandoc.read(html_text, format="html")
    result = pandoc.write(doc, "tmp/html_text.tex", format="latex")

    Path("tmp/html_text.tex").unlink()

    return result.rstrip()


def escape_chars(s):
    """Escape characters that are special in LaTeX"""
    s = s.replace("&", r"\&")
    s = s.replace("_", r"\_")
    s = s.replace("%", r"\%")
    s = s.replace("$", r"\$")
    s = s.replace("#", r"\#")
    s = s.replace("{", r"\{")
    s = s.replace("}", r"\}")
    s = s.replace("^", r"\textasciicircum{}")
    s = s.replace("[", "\[")
    s = s.replace("]", "\]")
    return s


def _make_authors_text(authors):
    """Make string displaying author information"""
    out = ""
    out += "\n" + r"\vspace{-1ex}{by " + "\small"
    for i, author in enumerate(authors):
        out += r"\textbf{\textcolor{AuthorColor}{\small "
        out += escape_chars(author["name"])
        out += "}}"

        out += r"$^{"
        out += escape_chars(str(author["affiliation"]))
        out += r"}$ "

        out += escape_chars(author["title"])

        if i != len(authors) - 1:
            out += r" $\mid$ "
        out += " "
    out += "}"
    return out


def _process_authors(authors):
    """Process the authors and affiliations"""
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
    out += r"{"
    for affiliation, affil_id in affiliations.items():
        out += (
            r"${}^"
            + str(affil_id)
            + r"$: "
            + escape_chars(affiliation)
            + r" \\ "
        )
    out += r"}"
    return out


def force_straight_quotes(text):
    """
    Enforce straight quotes to avoid issues with unmatched quotes
    """
    text = text.replace(r'" ', r"\textquotedbl{} ")
    text = text.replace(r'"', r"\textquotedbl ")
    return text


def remove_hypertarget(text):
    """
    Fixes bug with brk611 which has an embedded video.

    This removes the video entirely.
    """
    text = re.sub(r"\\hypertarget{.*?}", "", text)
    text = re.sub(r"\\includegraphics{.*?}", "", text)
    return text


def _get_img(data):
    """Download and save the image from the article"""
    tmp = Path("tmp")
    image_name = Path(data["image_path"]).name
    image_path = data["image_path"]
    if not image_path.startswith("http"):
        img_url = "https://thesciencebreaker.org/" + data["image_path"]
    else:
        img_url = image_path
    img_filename = tmp / image_name
    if img_filename.exists():
        logging.info("Image already downloaded, skipping")
        return image_name, 200

    logging.info("Downloading image %s", img_url)
    resp = requests.get(img_url)
    logging.info("Status code: %s", resp.status_code)
    if resp.status_code == 200:
        with open(img_filename, "wb") as f:
            f.write(resp.content)
        subprocess.run(
            ["convert", img_filename, "-colorspace", "RGB", img_filename],
        )

    return image_name, resp.status_code


def process_data(data):
    """
    Process the data from the API to make it ready for the LaTeX template.
    """
    template_data = {}

    main_text = html_to_latex(data["content"])
    main_text = force_straight_quotes(main_text)
    main_text = remove_hypertarget(main_text)
    template_data["mainText"] = main_text

    title = escape_chars(data["title"].replace("\n", " "))
    template_data["subjectTitle"] = title
    logging.info(f"Title: {title}")
    logging.info(f"DOI: {data['doi']}")
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
    template_data["authorText"] = _make_authors_text(authors)
    template_data["affiliationText"] = _make_affiliations_text(affiliations)
    template_data["editorName"] = f"scientific editor \# {data['editor_id']}"

    template_data["fileName"], status_code = _get_img(data)
    if status_code != 200:
        template_data["useImage"] = "\imagefalse"
    else:
        template_data["useImage"] = "\imagetrue"
    template_data["imageCredits"] = html_to_latex(data["image_credits"])

    template_data["citation"] = html_to_latex(data["original_article"])
    return template_data


def make_latex(template_data):
    """
    Make the latex file from the template and the data
    """
    tmp = Path("tmp")
    main_file = tmp / "main.tex"
    template = LATEX_JINJA_ENV.get_template(TEMPLATE_PATH.as_posix())

    with open(main_file, "w") as f:
        f.write(template.render(**template_data))


def make_pdf(data):
    """Make the pdf from the json file"""
    tmp = Path("tmp")
    tmp.mkdir(exist_ok=True)
    pdf_folder = Path("pdf")
    pdf_folder.mkdir(exist_ok=True)

    logging.info("Processing data")
    template_data = process_data(data)
    logging.info("Making LaTeX")
    make_latex(template_data)

    # Now we can compile the tex-file
    logging.info("Compiling PDF")
    tex_log = subprocess.run(
        ["xelatex", "-interaction=nonstopmode","-papersize=a4", "main.tex"],
        capture_output=True,
        cwd=tmp,
    )
    num_errors = 0
    for line in tex_log.stdout.decode("utf-8").split("\n"):
        if line.startswith("!"):
            logging.error("LaTeX error: " + line)
            num_errors += 1
    logging.info("Done compiling PDF, %d errors", num_errors)

    pdf_name = f"{data['slug']}.pdf"
    pdf_filename = pdf_folder / pdf_name
    os.rename(tmp / "main.pdf", pdf_filename)

    return pdf_filename.as_posix()
