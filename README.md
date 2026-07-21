# AgroAssist (NASA hackathon)

A Flask web app built for the NASA Space Apps Challenge that helps farmers share
resources and get agricultural advice. Users register an account, drop
location-tagged "circles" on a map to mark fields or plots, chat with other
farmers inside each circle, ask questions to an AI farming assistant, and view
NASA GLDAS soil moisture, surface temperature, and surface runoff data on an
interactive Plotly map.

A live deployment is at <https://farms.pythonanywhere.com/>.

## Features

- Account registration and login (Werkzeug password hashing, Flask sessions)
- Map of user-drawn circles that act as discussion rooms
- Per-circle chat stored in SQLite
- AgroAssist chatbot powered by OpenAI (GPT-3.5-turbo)
- `/plot/soil`, `/plot/temp`, and `/plot/sr` render NASA GLDAS NetCDF variables
  as Plotly scatter-mapbox figures

## Tech stack

Python 3.11, Flask, SQLite, Werkzeug, python-dotenv, OpenAI Python SDK, NumPy,
pandas, Plotly, netCDF4. Served in production with Gunicorn on PythonAnywhere.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then fill in SECRET_KEY and OPENAI_API_KEY

# The /plot/* routes read GLDAS NetCDF data. Download a .nc4 file from
# https://disc.gsfc.nasa.gov/datasets/GLDAS_CLSM025_DA1_2/summary and place it
# at the repo root as GLDAS_CLSM025_DA1_D.A20240529.022.nc4 (or edit the path
# in app/routes/main_routes.py). The rest of the app works without it.

flask --app run.py run --debug
# or: python run.py
```

The SQLite database (`users.db`) is created automatically on first run.

## Project layout

```
run.py                 entrypoint, creates the Flask app
app/__init__.py        app factory, blueprint registration, DB init
app/models.py          SQLite schema (users, circles, messages2)
app/routes/            auth, main, api, and chat blueprints
app/templates/         Jinja2 templates (home, login, register, chat, plot)
app/static/            images and CSS
```

## License

MIT. See [LICENSE](LICENSE). NASA GLDAS data is public domain and not
redistributed in this repository.
