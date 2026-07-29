# Tour Femmes Fantasy

A Flask fantasy cycling app for private games around ProCyclingStats-backed cycling events.

## What is included

- User login and registration.
- Active event overview cards with event status, user participation, team-selection status, and upcoming lineup status.
- Event pages with team selection before the first stage starts.
- Per-stage lineups, defaulting to 6 riders from an 11-rider event team, with one captain for double points.
- Weighted daily and final bonuses for the general, points, mountains, and youth classifications, including leader/winner teammate bonuses.
- Automatic lineup locking when a stage start time passes.
- Stage view with the route profile, the user's lineup, and imported results.
- Event leaderboard with total scores, latest-stage scores, per-stage columns, a CSS yellow jersey marker for the current leader, and stage-win badges.
- Event-specific private subleagues with shareable join codes and dedicated total and stage classifications.
- Admin pages protected by a simple password for creating events, managing users, loading PCS data locally, and safely merging local race data into production.
- A database model covering users, events, stages, teams, riders, selections, lineups, results, scores, live updates, and awards.

## Setup

The checked-in `.venv` on this machine points at a missing Python install, so create a fresh environment with an installed Python 3.12+:

```powershell
python -m venv .venv312
.\.venv312\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `SECRET_KEY` and `ADMIN_PASSWORD`.

Initialize the database:

```powershell
flask --app run.py init-db
```

Optional demo data:

```powershell
flask --app run.py seed-demo
```

Demo login after seeding:

- Username: `demo`
- Password: `demo`

Run locally:

```powershell
flask --app run.py run --debug
```

Open `http://127.0.0.1:5000`.

## PythonAnywhere deployment

For the production MySQL setup, WSGI configuration, and update procedure, see
[`PYTHONANYWHERE.md`](PYTHONANYWHERE.md).

## Admin Flow

1. Visit `/admin/login` and use `ADMIN_PASSWORD`.
2. Add an event with a PCS slug such as `tour-de-france-femmes` and year `2026`.
3. Open the event in admin and click `Initialize stages from PCS`.
4. Click `Sync current startlist`.
5. Open `Assign rider prices`, price every active rider, and save.
6. Users can now join the event and make selections.
7. Once PCS has ranked results, import them in the local admin; scores are recalculated locally.
8. Open the production admin and upload `instance/tour_femmes.sqlite3`.
9. Production merges only race data and recalculates scores from the online users' lineups.

## Notes

- Stage-result points are awarded by rank 1-18 and only those points are doubled for the captain. Classification and teammate bonuses are not doubled.
- Event `team_size` and `lineup_size` are stored on each event. Defaults are 11 and 6.
- PCS scraping is best-effort around their current URL patterns and page text. If PCS markup changes, importer errors should be handled in admin rather than silently changing game data.
- Use PCS responsibly and avoid aggressive automated polling.
- Both direct PCS actions and the database upload are available in every admin environment. On PythonAnywhere, use the database upload whenever PCS rejects a direct request.
- The production database upload never reads user, participation, team-selection, or stage-lineup tables from the local SQLite file.
