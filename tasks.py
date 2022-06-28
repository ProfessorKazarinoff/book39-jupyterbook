# tasks.py
"""
An invoke script to run build tasks for the book

$ invoke build website # this builds the mkdocs website website
 -- then cd into website directory and run mkdocs serve to view

$ invoke build pdf # this will eventually output a pdf/.tex file to complile with LaTeX to build a pdf
 -- then cd into pdf directory and use MikTek or other LaTeX complier to output a .pdf

"""

import datetime
import os
import re
import sys
from os import chdir, getcwd, listdir
from pathlib import Path
from shutil import copyfile, copytree, rmtree

import nbformat
from invoke import task
from nbconvert import LatexExporter
from nbconvert.preprocessors import RegexRemovePreprocessor
from nbconvert.writers import FilesWriter
from nbformat import NotebookNode
from pandocfilters import RawInline, applyJSONFilters


@task
def build(c):
    """
    a task to house the build command
    """
    print("Building...")
    print()


@task(help={"deploy": "Set --deploy for deployment on gh-pages"})
def jb(c, deploy=False):
    print("Building using Jupyter Book...")
    c.run("jb build --path-output website/ --verbose src")
    if deploy:
        c.run("ghp-import -n -p -f website/_build/html")


@task(help={"deploy": "Set --deploy for deployment on gh-pages"})
def jbtex(c, deploy=False):
    print("Building .tex file using Jupyter Book...")
    c.run("jb build --path-output pdf/ --builder latex --verbose src")


@task(help={"deploy": "Set --deploy for deployment on gh-pages"})
def website(c, deploy=False):
    """
    a task to build an mkdocs website from the src notebooks
    """
    t1 = datetime.datetime.now()
    print("Building mkdocs website from src notebooks...")
    if Path("website").is_dir():
        print("Found website directory, deleting...")
        rmtree("website")
    print("Creating empty website directory...")
    Path("website").mkdir(parents=True, exist_ok=True)
    mkdocs_config_template = Path("templates", "mkdocs", "mkdocs.yml")
    mkdocs_build_config = Path("website", "mkdocs.yml")
    preamble_template = Path("templates", "mkdocs", "preamble.py")
    preamble_file = Path("website", "preamble.py")
    mathjax_config_file = Path("templates", "mkdocs", "mathjax_config.js")
    extra_css_file = Path("templates", "mkdocs", "extra.css")
    print("Copying mkdocs.yml and preamble.py from templates/mkdocs/ to website/")
    copyfile(mkdocs_config_template, mkdocs_build_config)
    copyfile(preamble_template, preamble_file)
    print("Copying src/ into website/docs/")
    copytree(Path("src"), Path("website", "docs"))
    print("Copying mathjax_config.js into website/docs/javascripts/mathjax_config.js")
    Path("website", "docs", "js").mkdir(parents=True, exist_ok=True)
    copyfile(mathjax_config_file, Path("website", "docs", "js", "mathjax_config.js"))
    print("Copying extra.css into website/docs/css/extra.css")
    Path("website", "docs", "css").mkdir(parents=True, exist_ok=True)
    copyfile(extra_css_file, Path("website", "docs", "css", "extra.css"))
    print("Changing to website directory")
    chdir("website")
    print(f"Current working directory {getcwd()}")
    print("running mkdocs build...")
    print()
    c.run("mkdocs build")
    t2 = datetime.datetime.now()
    delta_t = t2 - t1
    print(
        f"\nWebsite build complete!!!     processed in: {str(delta_t).split(':')[-1]} seconds "
    )
    if deploy:
        print("Deploying to GitHub Pages...")
        c.run("mkdocs gh-deploy --force --verbose")


@task
def pdf(c):
    """
    a task to build a LaTeX .tex doc from the src notebooks
    """
    t1 = datetime.datetime.now()
    print("Building LaTeX .tex doc from src/ notebooks...")
    # create empty pdf/ and pdf/images/ directories
    make_empty_dir("pdf")
    print("Copying all images from src/subdir/images/ to pdf/images/")
    src_dir_path = Path("src")
    dest_images_dir_path = Path("pdf", "images")
    # copy all images from src/subdirs/images/ to pdf/images/
    copy_all_images(src_dir_path, dest_images_dir_path)
    # Build a list of all of the notebook paths.
    print("Creating a list of all notebook paths")
    nb_path_lst = iter_notebook_paths(src_dir_path)
    # merge all of the notebooks into one big notebook node.
    print("Merging all notebooks into one big notebook...")
    nbnode = merge_notebooks(nb_path_lst)
    # export notebook node into a .tex file using templates
    d = datetime.datetime.now()
    output_file_path = Path(
        os.getcwd(),
        "pdf",
        f"Problem_Solving_with_Python_39_Edition_{d:%Y}_{d:%m}_{d:%d}.tex",
    )
    template_file_path = Path(os.getcwd(), "templates", "latex", "book39.tex.j2")
    print("Attempting to produce a .tex file from the big combined notebook...")
    export_tex(nbnode, output_file_path, template_file_path)
    # modify TOC in .tex file so that chapter numbering works
    convert_TOC(output_file_path)
    # copy the copywrite and dedication page .tex files to the pdf/ dir
    f_names = ["copywrite_page.tex", "dedication_page.tex"]
    for f_name in f_names:
        copyfile(
            Path(os.getcwd(), "templates", "latex", f_name),
            Path(os.getcwd(), "pdf", f_name),
        )
        print(f"Coppied {f_name} to pdf/ directory")
    # Print the final output
    t2 = datetime.datetime.now()
    delta_t = t2 - t1
    print(
        f"Conversion complete!!!     processed in: {str(delta_t).split(':')[-1]} seconds \n Find the exported .tex file in: \n {output_file_path}"
    )


def convert_TOC(output_file_path: Path):
    print("Working on taking the Preface and Appendix out of the TOC... function not ready yet")
    chapter_list_exclude_from_TOC = ["Preface","Appendix"]
    section_list_exclude_from_TOC = [
        "Motivation",
        "Acknowledgmments",
        "Supporting Materials",
        "Formatting Convensions",
        "Errata",
        "Reserved and Key Words in Python",
        "ASCII Character Codes",
        "Virtual Environments",
        "NumPy Math Functions",
        "Git and GitHub",
        "LaTeX Math",
        "Problem Solving with Python Book Construction",
        "Contributions",
        "Cover Artwork",
        "About the Author",
    ]
    # latex_chapter_search_line = "\\" + "chapter" + "{" + f"{chapter}" + "}" + "\\" + "label" + "{" + f"{chapter.lower()}" + "}" "}"
    # latex_section_search_line = "\\" + "section" + "{" + f"{section}" + "}" + "\\" + "label" + "{" + f"{chapter.lower().replace(" ","-")}" + "}" "}"
            # \section{ASCII Character Codes}\label{ascii-character-codes}}

    """
    Put a * by the Preface chapter header and the Appendix chapter header. Follow with a line to add the chapter back to the table of contents.

\chapter*{Preface}\label{preface}
	\addcontentsline{toc}{chapter}{Preface}
Also do this with the sections of the preface. So the first section needs to be changed to

 \section*{Motivation}\label{motivation}
        \addcontentsline{toc}{section}{Motivation}
    """


def export_tex(
    combined_nb_node: NotebookNode, output_file_path: Path, template_file_path=None
):
    resources = {}
    resources["unique_key"] = "combined"
    resources["output_files_dir"] = "combined_files"
    exporter = MyLatexExporter(template_file=str(template_file_path))
    mypreprocessor = RegexRemovePreprocessor()
    mypreprocessor.patterns = ["\s*\Z"]
    exporter.register_preprocessor(mypreprocessor, enabled=True)
    writer = FilesWriter(build_directory=str(output_file_path.parent))
    output, resources = exporter.from_notebook_node(combined_nb_node, resources)
    writer.write(output, resources, notebook_name=output_file_path.stem)


def convert_link(key, val, fmt, meta):
    if key == "Link":
        target = val[2][0]
        # Links to other notebooks
        m = re.match(r"(\d+\-.+)\.ipynb$", target)
        if m:
            return RawInline("tex", "Chapter \\ref{sec:%s}" % m.group(1))

        # Links to sections of this or other notebooks
        m = re.match(r"(\d+\-.+\.ipynb)?#(.+)$", target)
        if m:
            # pandoc automatically makes labels for headings.
            label = m.group(2).lower()
            label = re.sub(r"[^\w-]+", "", label)  # Strip HTML entities
            return RawInline("tex", "Section \\ref{%s}" % label)

    # Other elements will be returned unchanged.


def convert_links(source):
    return applyJSONFilters([convert_link], source)


class MyLatexExporter(LatexExporter):
    def default_filters(self):
        yield from super().default_filters()
        yield ("resolve_references", convert_links)


def copy_all_images(source_dir_path, dest_images_dir_path):
    """
    a function to copy all the images from a main source dir that has sub dirs with images
    to a dest dir
    """
    REG_nb_dir = re.compile((r"(\d\d)-*"))
    REG_img_filename = re.compile(
        (r"([/|.|\w|\s|-])*\.(?:jpg|gif|png|tiff|jpeg|tif|pdf)")
    )

    if dest_images_dir_path.is_dir():
        print(f"Found {dest_images_dir_path} directory, deleting")
        rmtree(dest_images_dir_path)
    print(f"Creating empty {dest_images_dir_path} directory...")
    dest_images_dir_path.mkdir(parents=True, exist_ok=True)

    for sub_dir in listdir(source_dir_path):
        if REG_nb_dir.match(sub_dir):
            if os.path.exists(os.path.join(source_dir_path, sub_dir, "images")):
                sub_dir_path = Path(source_dir_path, sub_dir, "images")
                for f in os.listdir(sub_dir_path):
                    try:
                        if REG_img_filename.match(f):
                            copyfile(
                                Path(sub_dir_path, f), Path(dest_images_dir_path, f)
                            )
                            print(f"coppied image file {f}")
                    except IOError as e:
                        print(f"Unable to copy file. {f}")
                        exit(1)
                    except:
                        print("Unexpected error:", sys.exc_info())
                        exit(1)


def merge_notebooks(nb_path_lst):
    """
    a function that creates a single notebook node object from a list of notebook file paths
    :param filename_lst: lst, a list of .ipynb file paths
    :return: a single notebookNode object
    """
    merged = None
    for fname in nb_path_lst:
        with open(fname, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        if merged is None:
            merged = nb
        else:
            merged.cells.extend(nb.cells)
    if not hasattr(merged.metadata, "name"):
        merged.metadata.name = ""
    merged.metadata.name += "_merged"
    # print(nbformat.writes(merged))
    return merged


def iter_notebook_paths(src_dir_path):
    REG_nb = re.compile(r"(\d\d).(\d\d)-(.*)\.ipynb")
    REG_nb_dir = re.compile((r"(\d\d)-*"))
    nb_path_lst = []

    for sub_dir in listdir(src_dir_path):
        if REG_nb_dir.match(sub_dir):
            sub_dir_path = Path(src_dir_path, sub_dir)
            print(f"identified sub dir {sub_dir_path}")
            for f in os.listdir(sub_dir_path):
                if REG_nb.match(f):
                    nb_path_lst.append(Path(sub_dir_path, f))
                    print(f"added {f} to source notebook path list")
    return sorted(nb_path_lst)


def make_empty_dir(new_dir_name):
    """
    a function to create a new empty directory relative to the current working directory
    input:
        new_dir_name: string
    """
    if Path(new_dir_name).is_dir():
        print(f"Found {new_dir_name} directory, deleting...")
        rmtree(new_dir_name)
    print(f"Creating empty {new_dir_name} directory...")
    Path(new_dir_name).mkdir(parents=True, exist_ok=True)
