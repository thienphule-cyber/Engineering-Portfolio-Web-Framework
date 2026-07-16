# Engineering Portfolio Web Framework

A scalable personal portfolio website for showcasing engineering projects
(Robotics, Embedded Systems, AI, IoT, Automation, Mechanical Design).

Built with Python (Flask) + Jinja2 server-side rendering. Projects are
stored as individual JSON files and rendered through a shared template,
so new projects can be added without touching the codebase.

## Features

- Home page with featured projects
- Filterable project gallery by category
- Individual project detail pages (objective, architecture, hardware, software, engineering process)
- Add new projects directly through a web form (no manual file editing required)
- Zero-project state supported (site works before any project is added)

## Tech Stack

- **Backend:** Python 3, Flask
- **Templating:** Jinja2
- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Data storage:** JSON files (no database required)

## Project Structure
portfolio/
├── app.py                  # Flask application and routes
├── projects/                # Project data (one .json file per project)
├── templates/                # Jinja2 HTML templates
├── static/                   # CSS, JS, and uploaded assets
├── tests/                    # Automated tests
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development/testing dependencies
├── start.sh / stop.sh        # Server control scripts
└── README.md

## Getting Started

```bash
git clone <your-repo-url>
cd portfolio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

Or use the control scripts:

```bash
./start.sh   # start the server in the background
./stop.sh    # stop the server
```

## Adding a Project

Either:
1. Go to `/projects/new` on the running site and fill in the form, or
2. Copy `projects/_TEMPLATE.json.example`, rename it, and edit the fields manually.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Roadmap

- [ ] Image/video upload support for projects
- [ ] PostgreSQL backend for larger scale
- [ ] Admin authentication for project management
- [ ] Deployment to a cloud platform (Render/Railway)

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

Phill — Mechatronics Engineering Student