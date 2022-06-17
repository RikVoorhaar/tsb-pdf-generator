# %%
import os
import datetime
import shutil
import subprocess
import json


TMP_LOCATION = "tmp"

import jinja2

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
    loader=jinja2.FileSystemLoader(os.path.abspath(".")),
)
TEMPLATE_LOCATION = "templates/template.tex"

TMP_LOCATION = "tmp"


def make_tex(preamb_file, metadata_file):
    """Turn the data into a pdf"""
    try:
        os.mkdir("tmp")
    except FileExistsError:
        pass

    main_file = "tmp/main.tex"

    with open(metadata_file, "r") as f:
        metadata = json.load(f) 

    template = latex_jinja_env.get_template(TEMPLATE_LOCATION)

    date = metadata["date"]
    if date == "":
        today = datetime.date.today()
        date = today.strftime("%B %d, %Y")
    metadata["date"] = date

    authors = _process_authors(metadata)
    metadata["authorText"] = _make_authors_text(authors)

    affiliations = _process_affiliations(metadata)
    metadata["affiliationText"] = _make_affiliations_text(affiliations)

    metadata["subjectSelect"] = escape_ampersand(metadata["subjectSelect"])

    with open(main_file, "w") as f:
        f.write(template.render(**metadata))


def _process_authors(metadata):
    """Process the authors"""
    ids_ = []
    authors = []
    for key in metadata.keys():
        if key.startswith("author"):
            ids_.append("".join([s for s in key if s.isdigit()]))
    for id in ids_:
        author_name = (
            metadata["firstName" + id] + " " + metadata["lastName" + id]
        )
        if metadata["affiliation" + id].strip() != "":
            authors.append(
                {
                    "name": author_name,
                    "affiliation": metadata["affiliation" + id],
                    "title": metadata["authorTitle" + id],
                }
            )
    return authors


def _make_authors_text(authors):
    """Make string displaying author information"""
    out = ""
    out += "\n" + r"\vspace{-1ex}{by " + "\small"
    for i, author in enumerate(authors):
        out += r"\textbf{\textcolor{AuthorColor}{\small "
        out += author["name"]
        out += "}}"

        out += r"$^{"
        out += author["affiliation"]
        out += r"}$ "

        out += author["title"]

        if i != len(authors) - 1:
            out += r" $\mid$ "
        out += " "
    out += "}"
    return out


def _process_affiliations(metadata):
    """Process the affiliations"""
    affiliations = {}
    for key, value in metadata.items():
        if key.startswith("inputAffiliation"):
            id = "".join([s for s in key if s.isdigit()])
            if value.strip() != "":
                affiliations[id] = value
    return affiliations


def _make_affiliations_text(affiliations):
    """Insert the affiliations into the main file"""
    out = ""
    out += "\n" + r"{\footnotesize "
    for key, affiliation in affiliations.items():
        out += r"${}^" + key + r"$: " + affiliation + r"\\ "
    out += r"}"
    return out


def escape_ampersand(string):
    return string.replace("&", "\\&")


def make_pdf():
    make_tex(
        "preamb.tex",
        "tmp/metadata.json",
    )

    # Now we can compile the tex-file
    print("Compiling PDF...")
    tex_log = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
        capture_output=True,
        cwd=TMP_LOCATION,
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


if __name__ == "__main__":
    make_pdf()

# %%
