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

To copy the existing local database instead, upload the local file
`instance/tour_femmes.sqlite3` to:

`/home/YOUR_USERNAME/tour_femmes_import.sqlite3`

Then run:

```bash
flask --app run.py import-sqlite --source ~/tour_femmes_import.sqlite3
flask --app run.py db-stats
rm ~/tour_femmes_import.sqlite3
```

The import refuses to run when the target contains any records, preventing an
accidental duplicate or overwrite. Remove the uploaded SQLite copy only after
the table counts have been checked.

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

After a reload, open an admin event page and click **PCS verbinding testen**.
If a PCS request still fails, the flash message shows the failing endpoint and
the PythonAnywhere error log contains the full request error.

For `HTTP 403` there are two different cases:

- `Herkomst lijkt PythonAnywhere-proxy/allowlist`: the request is still being
  blocked before it reaches PCS. Confirm that `www.procyclingstats.com` is on
  the allowlist, then reload the web app from the **Web** tab.
- `Herkomst lijkt PCS/server` or `Herkomst lijkt PCS/Cloudflare`: the
  PythonAnywhere allowlist is working, but PCS is refusing the HTML request
  from the server. Images can still load in this case when
  `PCS_PROXY_IMAGES=false`, because visitors fetch them directly in their own
  browser instead of through PythonAnywhere.

When PCS/Cloudflare blocks server-side HTML requests, use the fallback on the
admin event page:

1. Open the relevant PCS page in your normal browser.
2. Save the page as HTML or copy the page source.
3. In **Handmatige PCS-import**, upload/paste that HTML for etappes,
   startlists, stage details, or results.

The fallback uses the same parsers and database writes as the automatic PCS
sync, but the PythonAnywhere server no longer has to fetch the PCS HTML itself.

## Important production notes

- PythonAnywhere does not support background threads in web workers. Production
  uses `INLINE_ADMIN_JOBS=true`, so large PCS imports run inside the admin
  request. Use rider-detail imports sparingly.
- Keep `PCS_BASE_URL=https://www.procyclingstats.com`. This exact host is on
  the PythonAnywhere allowlist. `PCS_PROXY_IMAGES=false` lets visitors load PCS
  images directly in their browser, avoiding slow server-side image proxy
  requests from the single uWSGI worker.
- PythonAnywhere closes idle MySQL connections after five minutes. The app uses
  SQLAlchemy connection pre-ping and a 280-second recycle interval.
- Keep `.env` and database exports outside Git.
- Back up MySQL regularly with `mysqldump` from a PythonAnywhere Bash console.
