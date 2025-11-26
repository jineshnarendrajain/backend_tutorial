# Flask Boilerplate

This repository contains a minimal Flask server boilerplate.

Files added:
- `app.py` - Flask application and `create_app()` factory
- `wsgi.py` - WSGI entry for production
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment variables

Quickstart (PowerShell):

```powershell
# create and activate a venv
python -m venv venv; .\venv\Scripts\Activate

# install dependencies
pip install -r requirements.txt

# copy environment example
copy .env.example .env

# run the app (development)
python app.py

# or run with gunicorn (production-like)
# pip install gunicorn
# gunicorn wsgi:application -b 0.0.0.0:5000
```

Endpoints:
- `GET /` → Welcome message
- `GET /health` → `{ "status": "ok" }`
- `POST /echo` → Echoes JSON body: `{ "received": ... }`

Next steps you might want:
- Add unit tests under a `tests/` folder
- Add Dockerfile and `docker-compose.yml` for local dev
- Add CI pipeline to run lint/tests

Feel free to ask me to add tests, Docker, or CI next.
sample readme