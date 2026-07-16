"""
Engineering Portfolio Web Framework
Main Flask application. Projects and contact info are now stored in
PostgreSQL (via SQLAlchemy) instead of local JSON files, so data
survives Render redeploys. Profile photo is still stored on disk
(see note in edit_photo route about its own limitation).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import Flask, render_template, abort, request, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import re

load_dotenv(dotenv_path=".env")  # reads .env when running locally; Render provides env vars directly

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

IMAGES_DIR = Path(__file__).parent / "static" / "assets" / "images"
PROFILE_PHOTO_FILENAME = "profile.jpg"
ALLOWED_PHOTO_EXTENSIONS = {"jpg", "jpeg"}

# ------------------------------------------------------------
# Database setup
# ------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, default="Other")
    objective = Column(Text, default="")
    problem = Column(Text, default="")
    # Stored as JSON-encoded text since these are lists of strings
    architecture = Column(Text, default="[]")
    hardware = Column(Text, default="[]")
    software = Column(Text, default="[]")
    process = Column(Text, default="[]")

    def to_dict(self):
        return {
            "slug": self.slug,
            "title": self.title,
            "category": self.category,
            "objective": self.objective,
            "problem": self.problem,
            "architecture": json.loads(self.architecture),
            "hardware": json.loads(self.hardware),
            "software": json.loads(self.software),
            "process": json.loads(self.process),
            "images": [],
            "videos": [],
            "documents": []
        }


class ContactInfo(Base):
    __tablename__ = "contact_info"

    id = Column(Integer, primary_key=True)
    email = Column(String, default="")
    phone = Column(String, default="")
    linkedin = Column(String, default="")
    github = Column(String, default="")


# Create tables if they don't exist yet (safe to run every startup)
Base.metadata.create_all(engine)


# ------------------------------------------------------------
# Project helpers
# ------------------------------------------------------------

def load_all_projects():
    """Load all projects from the database."""
    session = SessionLocal()
    try:
        projects = session.query(Project).order_by(Project.title).all()
        return [p.to_dict() for p in projects]
    finally:
        session.close()


def load_project(slug):
    """Load a single project by slug from the database."""
    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(slug=slug).first()
        return project.to_dict() if project else None
    finally:
        session.close()


def save_new_project(slug, data):
    """Insert a new project row into the database."""
    session = SessionLocal()
    try:
        new_project = Project(
            slug=slug,
            title=data["title"],
            category=data["category"],
            objective=data["objective"],
            problem=data["problem"],
            architecture=json.dumps(data["architecture"]),
            hardware=json.dumps(data["hardware"]),
            software=json.dumps(data["software"]),
            process=json.dumps(data["process"])
        )
        session.add(new_project)
        session.commit()
    finally:
        session.close()


def update_existing_project(slug, data):
    """Update an existing project row in the database."""
    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(slug=slug).first()
        if project is None:
            return False
        project.title = data["title"]
        project.category = data["category"]
        project.objective = data["objective"]
        project.problem = data["problem"]
        project.architecture = json.dumps(data["architecture"])
        project.hardware = json.dumps(data["hardware"])
        project.software = json.dumps(data["software"])
        project.process = json.dumps(data["process"])
        session.commit()
        return True
    finally:
        session.close()


def delete_project_by_slug(slug):
    """Delete a project row from the database."""
    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(slug=slug).first()
        if project is None:
            return False
        session.delete(project)
        session.commit()
        return True
    finally:
        session.close()


def slugify(title):
    """Convert a project title into a URL-safe, filename-safe slug."""
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug or "untitled_project"


def lines_to_list(text):
    """Convert a multi-line textarea input into a list of strings."""
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def list_to_lines(items):
    """Convert a list of strings back into newline-joined text."""
    if not items:
        return ""
    return "\n".join(items)


# ------------------------------------------------------------
# Contact info helpers
# ------------------------------------------------------------

def load_contact_info():
    """Load the single contact info row from the database.
    Creates a default empty row on first use."""
    session = SessionLocal()
    try:
        contact = session.query(ContactInfo).first()
        if contact is None:
            contact = ContactInfo(email="", phone="", linkedin="", github="")
            session.add(contact)
            session.commit()
        return {
            "email": contact.email,
            "phone": contact.phone,
            "linkedin": contact.linkedin,
            "github": contact.github
        }
    finally:
        session.close()


def save_contact_info(data):
    """Update the single contact info row in the database."""
    session = SessionLocal()
    try:
        contact = session.query(ContactInfo).first()
        if contact is None:
            contact = ContactInfo()
            session.add(contact)
        contact.email = data["email"]
        contact.phone = data["phone"]
        contact.linkedin = data["linkedin"]
        contact.github = data["github"]
        session.commit()
    finally:
        session.close()


# ------------------------------------------------------------
# Profile photo helpers (still file-based, see note in edit_photo route)
# ------------------------------------------------------------

def is_allowed_photo(filename):
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_PHOTO_EXTENSIONS


def profile_photo_exists():
    return (IMAGES_DIR / PROFILE_PHOTO_FILENAME).exists()


# ------------------------------------------------------------
# Routes: general pages
# ------------------------------------------------------------

@app.route("/")
def home():
    projects = load_all_projects()
    return render_template("index.html", projects=projects)


@app.route("/about")
def about():
    has_photo = profile_photo_exists()
    return render_template("about.html", has_photo=has_photo)


@app.route("/about/edit-photo", methods=["GET", "POST"])
def edit_photo():
    """Upload/replace the profile photo.
    NOTE: this still writes to local disk, which is ephemeral on Render's
    free tier. The photo will be lost on redeploy unless you upgrade to a
    paid instance with a Persistent Disk, or store the photo in the
    database as binary data instead."""
    if request.method == "POST":
        uploaded_file = request.files.get("photo")

        if uploaded_file is None or uploaded_file.filename == "":
            flash("No file selected.")
            return redirect(url_for("edit_photo"))

        if not is_allowed_photo(uploaded_file.filename):
            flash("Only .jpg or .jpeg files are allowed.")
            return redirect(url_for("edit_photo"))

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        destination = IMAGES_DIR / PROFILE_PHOTO_FILENAME
        uploaded_file.save(destination)

        flash("Profile photo updated successfully.")
        return redirect(url_for("about"))

    has_photo = profile_photo_exists()
    return render_template("edit_photo.html", has_photo=has_photo)


# ------------------------------------------------------------
# Routes: projects
# ------------------------------------------------------------

@app.route("/projects")
def gallery():
    projects = load_all_projects()
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

        if load_project(slug) is not None:
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
            "process": process
        }

        save_new_project(slug, project_data)
        return redirect(url_for("project_detail", slug=slug))

    return render_template("add_project.html", form_data={})


@app.route("/projects/<slug>/edit", methods=["GET", "POST"])
def edit_project(slug):
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
            return render_template("edit_project.html", form_data=request.form, slug=slug)

        updated_data = {
            "title": title,
            "category": category or "Other",
            "objective": objective,
            "problem": problem,
            "architecture": architecture,
            "hardware": hardware,
            "software": software,
            "process": process
        }

        update_existing_project(slug, updated_data)
        flash("Project updated successfully.")
        return redirect(url_for("project_detail", slug=slug))

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
    if not delete_project_by_slug(slug):
        abort(404)
    flash("Project deleted.")
    return redirect(url_for("gallery"))


# ------------------------------------------------------------
# Routes: contact
# ------------------------------------------------------------

@app.route("/contact")
def contact():
    contact_info = load_contact_info()
    return render_template("contact.html", contact=contact_info)


@app.route("/contact/edit", methods=["GET", "POST"])
def edit_contact():
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

    contact_info = load_contact_info()
    return render_template("edit_contact.html", contact=contact_info)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=False, host="0.0.0.0", port=port)