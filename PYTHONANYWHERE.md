# Deploying Tour Femmes Fantasy to PythonAnywhere

This deployment uses a PythonAnywhere MySQL database. SQLite remains the
default for local development.

## 1. Create the PythonAnywhere resources

Create a PythonAnywhere account and note whether it is on:

- `www.pythonanywhere.com` (global/US), or
- `eu.pythonanywhere.com` (EU).

On the **Databases** tab, create a MySQL database named `tour_femmes`.
PythonAnywhere will display the database hostname. The complete database name
will be `YOUR_USERNAME$tour_femmes`.

## 2. Clone and install

Open a PythonAnywhere Bash console:

```bash
git clone https://github.com/VeerkampAidEnvironment/wielrennen-fanttasy.git
cd wielrennen-fanttasy
python3.13 -m venv ~/.virtualenvs/tour-femmes
source ~/.virtualenvs/tour-femmes/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If Python 3.13 is not offered for the web app, use the same available Python
version for both the virtual environment and web app.

## 3. Configure secrets and MySQL

Create `/home/YOUR_USERNAME/wielrennen-fanttasy/.env`:

```dotenv
SECRET_KEY=GENERATE_A_LONG_RANDOM_VALUE
ADMIN_PASSWORD=CHOOSE_A_STRONG_ADMIN_PASSWORD
DATABASE_URL=mysql+pymysql://YOUR_USERNAME:URL_ENCODED_MYSQL_PASSWORD@YOUR_MYSQL_HOST/YOUR_USERNAME$tour_femmes
PCS_BASE_URL=https://www.procyclingstats.com
APP_TIMEZONE=Europe/Amsterdam
AUTO_CREATE_SCHEMA=false
INLINE_ADMIN_JOBS=true
PCS_PROXY_IMAGES=false
PCS_DATABASE_UPLOAD_MAX_BYTES=134217728
```

Generate the secret from the Bash console:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The MySQL password in `DATABASE_URL` must be URL-encoded. Generate the encoded
form without printing any other configuration:

```bash
python -c "from urllib.parse import quote_plus; print(quote_plus(input('MySQL password: ')))"
```

Do not commit `.env`; it is already ignored by Git.

## 4. Initialize the live database

From the repository directory with the virtual environment active:

```bash
flask --app run.py init-db
```

Do not replace the production MySQL database with the local SQLite database.
Accounts and game choices live only in production once friends start playing.

The normal PCS update flow is:

1. Run the app locally.
2. Load or refresh PCS stages, startlists, rider profiles, and results in the
   local admin.
3. Open the production admin dashboard.
4. In **Koersdata naar de online database**, upload the local file
   `instance/tour_femmes.sqlite3`.
5. Wait for the success message before reloading the web app.

The upload reads only events, stages, teams, riders, event startlists, stage
results, and classification results. It never reads or replaces users,
participations, team selections, stage lineups, user scores, or awards from the
local database. Existing production IDs are preserved. After result imports,
scores and awards are recalculated from the production users' own lineups. The
whole merge is committed as one transaction; a failure rolls it back.

Do not run `seed-demo` for the real site unless demo accounts and data are
actually wanted.

## 5. Create the web app

On the **Web** tab:

1. Add a new web app using **Manual configuration**.
2. Select the same Python version as the virtual environment.
3. Set the virtualenv path to `/home/YOUR_USERNAME/.virtualenvs/tour-femmes`.
4. Edit the WSGI configuration file to contain:

```python
import sys

project_path = "/home/YOUR_USERNAME/wielrennen-fanttasy"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from pythonanywhere_wsgi import application
```

5. Reload the web app.

The site will be available at `YOUR_USERNAME.pythonanywhere.com`.

## Updating the application

After pushing changes from PyCharm:

```bash
cd ~/wielrennen-fanttasy
git pull --ff-only
source ~/.virtualenvs/tour-femmes/bin/activate
pip install -r requirements.txt
```

Then reload the web app from PythonAnywhere's **Web** tab. Database content is
stored separately in MySQL and is not replaced by `git pull`.

After a reload, both the direct PCS buttons and the database upload are
available in production admin. If PCS rejects a direct server-side request,
load the data locally and use the database upload.

## Important production notes

- Direct PCS requests remain available in production, but PythonAnywhere may
  still receive a PCS or Cloudflare 403. The database upload is the reliable
  fallback for that situation.
- Keep `PCS_BASE_URL=https://www.procyclingstats.com`. This exact host is on
  the PythonAnywhere allowlist. `PCS_PROXY_IMAGES=false` lets visitors load PCS
  images directly in their browser, avoiding slow server-side image proxy
  requests from the single uWSGI worker.
- PythonAnywhere closes idle MySQL connections after five minutes. The app uses
  SQLAlchemy connection pre-ping and a 280-second recycle interval.
- Keep `.env` and database exports outside Git.
- The uploaded SQLite file is stored only in a temporary server file and is
  deleted after the import attempt.
- Back up MySQL regularly with `mysqldump` from a PythonAnywhere Bash console.
