"""
Engineering Portfolio Web Framework
Main Flask application: loads project data from JSON files
and renders them through Jinja2 templates.

Projects are stored as individual .json files inside projects/.
Contact info is stored in a single contact_info.json file.
Both projects and contact info can be created/edited through the web UI.
"""

import json
import re
from pathlib import Path
from flask import Flask, render_template, abort, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # needed for flash messages

PROJECTS_DIR = Path(__file__).parent / "projects"
CONTACT_FILE = Path(__file__).parent / "contact_info.json"


# ------------------------------------------------------------
# Project helpers
# ------------------------------------------------------------

def load_all_projects():
    """Load all project JSON files from the projects/ directory.
    Returns an empty list if no project files exist yet."""
    projects = []
    for file in sorted(PROJECTS_DIR.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["slug"] = file.stem  # filename without extension = URL slug
            projects.append(data)
    return projects


def load_project(slug):
    """Load a single project by its slug (filename without extension)."""
    file_path = PROJECTS_DIR / f"{slug}.json"
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data["slug"] = slug
        return data


def save_project(slug, project_data):
    """Write project data to its JSON file, identified by slug."""
    file_path = PROJECTS_DIR / f"{slug}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)


def slugify(title):
    """Convert a project title into a URL-safe, filename-safe slug.
    Example: 'Autonomous Vehicle!' -> 'autonomous_vehicle'"""
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)   # remove special characters
    slug = re.sub(r"[\s-]+", "_", slug)        # spaces/dashes -> underscore
    return slug or "untitled_project"


def lines_to_list(text):
    """Convert a multi-line textarea input into a clean list of strings,
    skipping empty lines."""
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def list_to_lines(items):
    """Convert a list of strings back into newline-joined text,
    used to pre-fill textareas when editing an existing project."""
    if not items:
        return ""
    return "\n".join(items)


# ------------------------------------------------------------
# Contact info helpers
# ------------------------------------------------------------

def load_contact_info():
    """Load contact info from contact_info.json.
    Returns safe empty defaults if the file does not exist yet."""
    if not CONTACT_FILE.exists():
        return {"email": "", "phone": "", "linkedin": "", "github": ""}
    with open(CONTACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contact_info(data):
    """Write contact info to contact_info.json."""
    with open(CONTACT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------
# Routes: general pages
# ------------------------------------------------------------

@app.route("/")
def home():
    projects = load_all_projects()
    return render_template("index.html", projects=projects)


@app.route("/about")
def about():
    return render_template("about.html")


# ------------------------------------------------------------
# Routes: projects
# ------------------------------------------------------------

@app.route("/projects")
def gallery():
    projects = load_all_projects()
    # Unique category list for the filter buttons (empty if no projects yet)
    categories = sorted(set(p.get("category", "Other") for p in projects))
    return render_template("gallery.html", projects=projects, categories=categories)


@app.route("/projects/<slug>")
def project_detail(slug):
    project = load_project(slug)
    if project is None:
        abort(404)
    return render_template("project_detail.html", project=project)


@app.route("/projects/new", methods=["GET", "POST"])
def add_project():
    """Display the add-project form (GET) and handle its submission (POST)."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        objective = request.form.get("objective", "").strip()
        problem = request.form.get("problem", "").strip()
        architecture = lines_to_list(request.form.get("architecture", ""))
        hardware = lines_to_list(request.form.get("hardware", ""))
        software = lines_to_list(request.form.get("software", ""))
        process = lines_to_list(request.form.get("process", ""))

        if not title:
            flash("Project title is required.")
            return render_template("add_project.html", form_data=request.form)

        slug = slugify(title)
        file_path = PROJECTS_DIR / f"{slug}.json"

        # Avoid overwriting an existing project with the same slug
        if file_path.exists():
            flash(f"A project with slug '{slug}' already exists. Choose a different title.")
            return render_template("add_project.html", form_data=request.form)

        project_data = {
            "title": title,
            "category": category or "Other",
            "objective": objective,
            "problem": problem,
            "architecture": architecture,
            "hardware": hardware,
            "software": software,
            "process": process,
            "images": [],
            "videos": [],
            "documents": []
        }

        save_project(slug, project_data)
        return redirect(url_for("project_detail", slug=slug))

    # GET request: show empty form
    return render_template("add_project.html", form_data={})


@app.route("/projects/<slug>/edit", methods=["GET", "POST"])
def edit_project(slug):
    """Display the edit form pre-filled with existing project data (GET),
    and save changes back to the same JSON file (POST).
    Note: the slug (and therefore the URL/filename) does not change even
    if the title is edited, so existing links to this project keep working."""
    project = load_project(slug)
    if project is None:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        objective = request.form.get("objective", "").strip()
        problem = request.form.get("problem", "").strip()
        architecture = lines_to_list(request.form.get("architecture", ""))
        hardware = lines_to_list(request.form.get("hardware", ""))
        software = lines_to_list(request.form.get("software", ""))
        process = lines_to_list(request.form.get("process", ""))

        if not title:
            flash("Project title is required.")
            # Keep the slug in the form so re-rendering still points to the right project
            request.form = request.form.copy()
            return render_template("edit_project.html", form_data=request.form, slug=slug)

        updated_data = {
            "title": title,
            "category": category or "Other",
            "objective": objective,
            "problem": problem,
            "architecture": architecture,
            "hardware": hardware,
            "software": software,
            "process": process,
            # Preserve existing asset references (images/videos/documents)
            "images": project.get("images", []),
            "videos": project.get("videos", []),
            "documents": project.get("documents", [])
        }

        save_project(slug, updated_data)
        flash("Project updated successfully.")
        return redirect(url_for("project_detail", slug=slug))

    # GET request: pre-fill form with existing project data,
    # converting list fields back into newline-separated text for the textareas.
    form_data = {
        "title": project.get("title", ""),
        "category": project.get("category", ""),
        "objective": project.get("objective", ""),
        "problem": project.get("problem", ""),
        "architecture": list_to_lines(project.get("architecture", [])),
        "hardware": list_to_lines(project.get("hardware", [])),
        "software": list_to_lines(project.get("software", [])),
        "process": list_to_lines(project.get("process", []))
    }
    return render_template("edit_project.html", form_data=form_data, slug=slug)


@app.route("/projects/<slug>/delete", methods=["POST"])
def delete_project(slug):
    """Delete a project's JSON file. Triggered from the project detail page."""
    file_path = PROJECTS_DIR / f"{slug}.json"
    if not file_path.exists():
        abort(404)
    file_path.unlink()
    flash("Project deleted.")
    return redirect(url_for("gallery"))


# ------------------------------------------------------------
# Routes: contact
# ------------------------------------------------------------

@app.route("/contact")
def contact():
    """Display the contact page using data from contact_info.json."""
    contact_info = load_contact_info()
    return render_template("contact.html", contact=contact_info)


@app.route("/contact/edit", methods=["GET", "POST"])
def edit_contact():
    """Display the contact edit form (GET) and save changes (POST)."""
    if request.method == "POST":
        updated_info = {
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "linkedin": request.form.get("linkedin", "").strip(),
            "github": request.form.get("github", "").strip()
        }
        save_contact_info(updated_info)
        flash("Contact information updated successfully.")
        return redirect(url_for("contact"))

    # GET request: pre-fill form with current contact info
    contact_info = load_contact_info()
    return render_template("edit_contact.html", contact=contact_info)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)