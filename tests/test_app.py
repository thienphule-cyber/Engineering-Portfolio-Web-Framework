import json
import shutil
import pytest
from pathlib import Path

import app as flask_app_module

@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provides a Flask test client backed by a temporary, isolated
    projects/ directory so tests never touch real project data."""
    temp_projects_dir = tmp_path / "projects"
    temp_projects_dir.mkdir()

    # Redirect the app's PROJECTS_DIR to the temporary folder for this test
    monkeypatch.setattr(flask_app_module, "PROJECTS_DIR", temp_projects_dir)

    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as test_client:
        yield test_client, temp_projects_dir

def test_home_page_loads(client):
    test_client, _ = client
    response = test_client.get("/")
    assert response.status_code == 200

def test_about_page_loads(client):
    test_client, _ = client
    response = test_client.get("/about")
    assert response.status_code == 200


def test_contact_page_loads(client):
    test_client, _ = client
    response = test_client.get("/contact")
    assert response.status_code == 200

def test_gallery_empty_state(client):
    """Gallery should load fine and show the empty state when there are no projects."""
    test_client, _ = client
    response = test_client.get("/projects")
    assert response.status_code == 200
    assert b"No projects yet" in response.data


def test_project_detail_404_for_missing_slug(client):
    test_client, _ = client
    response = test_client.get("/projects/does-not-exist")
    assert response.status_code == 404

def test_add_project_via_form(client):
    """Submitting the add-project form should create a JSON file
    and redirect to the new project's detail page."""
    test_client, projects_dir = client

    form_data = {
        "title": "Test Robot Arm",
        "category": "Robotics",
        "objective": "Test objective",
        "problem": "Test problem",
        "architecture": "Step 1\nStep 2",
        "hardware": "Servo\nArduino",
        "software": "Python\nROS2",
        "process": "Design\nTest"
    }

    response = test_client.post("/projects/new", data=form_data, follow_redirects=True)
    assert response.status_code == 200

    created_file = projects_dir / "test_robot_arm.json"
    assert created_file.exists()

    with open(created_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["title"] == "Test Robot Arm"
    assert saved_data["hardware"] == ["Servo", "Arduino"]

def test_add_project_requires_title(client):
    """Submitting the form without a title should not create a file."""
    test_client, projects_dir = client

    response = test_client.post("/projects/new", data={"title": ""})
    assert response.status_code == 200  # re-renders the form
    assert list(projects_dir.glob("*.json")) == []


def test_duplicate_slug_rejected(client):
    """Adding two projects with the same title should not overwrite the first."""
    test_client, projects_dir = client

    form_data = {"title": "Duplicate Project", "category": "Robotics"}
    test_client.post("/projects/new", data=form_data)
    test_client.post("/projects/new", data=form_data)

    matching_files = list(projects_dir.glob("duplicate_project.json"))
    assert len(matching_files) == 1