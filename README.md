# Tour Femmes Fantasy

A Flask fantasy cycling app for private games around ProCyclingStats-backed cycling events.

## What is included

- User login and registration.
- Active event overview cards with event status, user participation, team-selection status, and upcoming lineup status.
- Event pages with team selection before the first stage starts.
- Per-stage lineups, defaulting to 6 riders from an 11-rider event team, with one captain for double points.
- Automatic lineup locking when a stage start time passes.
- Stage view that embeds a safe, auto-refreshing copy of the current day's PCS LiveStats dashboard until ranked results are imported.
- Event leaderboard with total scores, latest-stage scores, per-stage columns, a CSS yellow jersey marker for the current leader, and stage-win badges.
- Admin pages protected by a simple password for creating events, initializing stages from PCS, syncing startlists, freezing removed riders, assigning prices, and importing live/results.
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

## Admin Flow

1. Visit `/admin/login` and use `ADMIN_PASSWORD`.
2. Add an event with a PCS slug such as `tour-de-france-femmes` and year `2026`.
3. Open the event in admin and click `Initialize stages from PCS`.
4. Click `Sync current startlist`.
5. Open `Assign rider prices`, price every active rider, and save.
6. Users can now join the event and make selections.
7. On the stage day, the LiveStats viewer refreshes automatically; admins can also force an immediate refresh.
8. Once PCS has ranked results, admins can import results and scores are recalculated.

## Notes

- The scorer is intentionally simple because no point table was specified yet. It awards stage points by rank 1-18 and doubles the captain's rider points.
- Event `team_size` and `lineup_size` are stored on each event. Defaults are 11 and 6.
- PCS scraping is best-effort around their current URL patterns and page text. If PCS markup changes, importer errors should be handled in admin rather than silently changing game data.
- Use PCS responsibly and avoid aggressive automated polling.
