# GrowHigh

Smart Diploma Student Career, ECET & Job Management System.

- **Frontend:** React 18, Bootstrap 5, react-router 6, axios (`09_Frontend/growhigh-frontend`)
- **Backend:** Django 5.2, Django REST Framework, PostgreSQL, JWT (`08_Backend/growhigh-backend`)
- **API docs:** Swagger at `http://localhost:8000/api/docs/` while the backend runs

## Run it locally (Windows Command Prompt)

Backend:
```
cd 08_Backend\growhigh-backend
py -m venv venv
venv\Scripts\activate
pip install -r requirements\dev.txt
copy .env.example .env
py manage.py migrate
py manage.py seed_academics
py manage.py create_admin growhigh --password "YourPassword1" --email you@example.com
py manage.py runserver
```
Set `DB_PASSWORD` and `SECRET_KEY` in `.env` first, and create the `growhigh` PostgreSQL database.

Frontend (a second window):
```
cd 09_Frontend\growhigh-frontend
npm install
npm start
```

## Tests
```
cd 08_Backend\growhigh-backend
py manage.py test
```

## Useful commands
- `py manage.py import_curriculum --file seed/curriculum_C23_CSE.json`: subjects and topics
- `py manage.py import_questions --file seed/questions_C23_common.json`: questions
- `py manage.py import_papers --folder papers`: previous-year papers

Roles: Student, Faculty, Admin, Company. Secrets live in `.env`, which is never committed.
