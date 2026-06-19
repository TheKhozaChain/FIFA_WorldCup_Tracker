# wctracker — live WC2026 advancement tracker

[![tests](https://github.com/TheKhozaChain/FIFA_WorldCup_Tracker/actions/workflows/tests.yml/badge.svg)](https://github.com/TheKhozaChain/FIFA_WorldCup_Tracker/actions/workflows/tests.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small, open-source CLI that tracks **World Cup 2026 group-stage advancement
probabilities** and updates itself from real results every time you run it.

Each run fetches the latest group-stage results, recomputes every team's chance
of reaching the Round of 32 via **Monte Carlo simulation**, and prints a table
sorted by the change (**Δ**) against a frozen pre-tournament baseline. Run it
today and again tomorrow and the numbers move on their own as matches are
played — no manual data entry.

> **Scope note.** This tracks advancement out of the **48-team finals group
> stage** (12 groups of 4 → top 2 + 8 best third-placed = 32 teams), which the
> prompt calls "qualification". It is *not* the regional qualifiers that decide
> who reaches the finals.

```
           WC2026 Advancement Tracker — Group A
┏━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Team           ┃ Grp ┃ Pos ┃  Start ┃    Now ┃       Δ ┃
┡━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ Mexico         │  A  │  1  │  85.3% │ 100.0% │ ▲ +14.7 │
│ Korea Republic │  A  │  2  │  74.7% │  85.0% │ ▲ +10.3 │
│ South Africa   │  A  │  4  │  45.3% │  27.2% │ ▼ -18.1 │
│ Czechia        │  A  │  3  │  67.6% │  30.2% │ ▼ -37.3 │
└────────────────┴─────┴─────┴────────┴────────┴─────────┘
```

## Run it in 30 seconds

**Prerequisites:** Python 3.9+ and git.
- **Windows:** install [Python](https://www.python.org/downloads/windows/) (tick
  **"Add python.exe to PATH"** in the installer) and [Git for Windows](https://git-scm.com/download/win).
- **macOS:** `brew install python git`, or grab them from python.org / git-scm.com.

Then copy-paste the block for your system. It prints the table immediately from a
bundled snapshot of the **real** group-stage results (frozen 2026-06-19) — no API
key needed to try it.

> **Don't have git?** You can skip it: on the GitHub page click the green
> **Code ▾** button → **Download ZIP**, unzip it, then open a terminal in that
> folder and run the commands below starting from the `python -m venv` line.

**Windows (PowerShell):**

```powershell
git clone https://github.com/TheKhozaChain/FIFA_WorldCup_Tracker.git
cd FIFA_WorldCup_Tracker
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m wctracker --provider offline
```

**macOS / Linux:**

```bash
git clone https://github.com/TheKhozaChain/FIFA_WorldCup_Tracker.git
cd FIFA_WorldCup_Tracker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m wctracker --provider offline
```

**Coming back later?** Install is one-time. To run again, just re-activate the
environment first (needed in each new terminal window) and run:

| | Activate | Run |
| --- | --- | --- |
| **Windows** | `.venv\Scripts\Activate.ps1` | `python -m wctracker` |
| **macOS / Linux** | `source .venv/bin/activate` | `python -m wctracker` |

Your prompt shows `(.venv)` when the environment is active.

> **Windows tip:** if PowerShell blocks the activate script with a "running
> scripts is disabled" error, run this once, then retry:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. (Or use `cmd` instead,
> where the command is `.venv\Scripts\activate.bat`.)

## Get live, real-time data (free, ~2 minutes)

The offline snapshot is frozen at a date, so it goes stale. For **live numbers
that update themselves** as matches are played, each person gets their own free
API key (it's free forever, no card, 10 requests/minute — plenty):

1. **Register:** open **https://www.football-data.org/client/register**
   (keep the `www.` — without it some browsers/VPNs flag a certificate
   mismatch). Enter your email, pick **Python**, accept the terms.
2. **Check your email** — you'll get an API token (a long string) within a minute.
3. **Create your `.env` file** in the project folder:
   - **Windows (PowerShell):** `Copy-Item .env.example .env`
   - **macOS / Linux:** `cp .env.example .env`
4. **Paste your token** into `.env` so the first line reads:
   `FOOTBALL_DATA_API_KEY=your_token_here` (open `.env` in any text editor —
   Notepad is fine).
5. **Run it live:**

```
python -m wctracker --refresh      # fetches the latest results, updates the table
python -m wctracker                # reuses the cached data (no API call) for ~1 hour
```

That's everything. If a live fetch ever fails (no key, rate limit, no internet),
the tool automatically falls back to the bundled snapshot, so it always prints
something. `.env` is gitignored — your key stays on your machine.

## Usage

```
python -m wctracker [options]

  --provider {football-data,thesportsdb,offline}
                        data source (default: $WCTRACKER_PROVIDER or football-data)
  --refresh             ignore the local cache and re-fetch
  --sims N              number of Monte Carlo simulations (default 10000)
  --seed N              RNG seed for reproducible output
  --group X             filter to a single group, e.g. --group C
  --home-advantage F    override the home-team Elo nudge (default 30)
  --no-markdown         don't write latest.md
  --version
```

The table includes a **Status** column — `✓ in` once a team is certain to
advance in every simulation, `✗ out` once it's eliminated, `· live` otherwise.

Every run also prints a generated **"Headline movements"** commentary — who's
through, the biggest risers and fallers (and where the damage is clustered), the
best-third bubble, and anyone eliminated. It's rule-based and deterministic (no
LLM, no network), so it updates automatically as new results land.

Both the table and the commentary are also written to **`latest.md`**, ready to
share or commit.

## Data source

The data layer sits behind a small `DataProvider` interface
(`wctracker/providers/base.py`), so switching providers is a one-file change.

| Provider | Free tier | Coverage | Auth | Role |
| --- | --- | --- | --- | --- |
| **football-data.org** | 10 req/min | One call returns every group fixture + score, with group labels | `X-Auth-Token` header | **Default** |
| API-Football (api-sports.io) | 100 req/day | Very broad | API key header | Easy to add as another provider |
| TheSportsDB | loose, test key `3` | Variable; weaker live standings | key in URL | Bundled fallback example |
| _offline_ | — | Real results, frozen at a date | none | Zero-setup default + tests |

**Why football-data.org is the default:** a single authenticated GET to
`/competitions/WC/matches` returns every group-stage fixture with its group and
full-time score, so the whole tournament is built from **one request** —
comfortably inside the 10-req/min free tier. Auth is a single header, and the
JSON is clean. The trade-off: free tiers can lag live scores slightly, and exact
competition availability should be confirmed against your key's plan.

Results are **cached** to `data/cache/<provider>.json` (gitignored) for one hour
so ordinary re-runs cost no API quota; `--refresh` forces a re-fetch.

## How the probabilities work

Short version: played matches build the current standings; a **Poisson goal
model** seeded from Elo-style team ratings simulates every remaining fixture
`N` times; each run resolves **top-2-per-group + 8-best-third-placed**; a team's
probability is the share of runs it advances. The **baseline** is the same model
with zero matches played, frozen in `data/baseline.json`.

The best-third-placed cross-group comparison (points → goal difference → goals
scored) is the tricky part and is covered by dedicated tests. Full details and
assumptions: **[docs/methodology.md](docs/methodology.md)**.

## Project layout

```
wctracker/
  cli.py            # argument parsing + orchestration
  types.py          # Match / Tournament / TeamRecord
  fixtures.py       # round-robin schedule for a group of 4
  providers/        # DataProvider interface, football-data, thesportsdb, offline, cache, factory
  model/            # strength (Elo→Poisson), standings, tiebreak, simulate (Monte Carlo)
  report/           # rich terminal table + markdown writer
  data/             # ratings.json, snapshot.json
data/
  baseline.json     # frozen pre-tournament probabilities
  cache/            # local API cache (gitignored)
scripts/            # build_snapshot.py, build_baseline.py (maintenance)
docs/methodology.md
tests/              # standings, tiebreak, simulation
```

## Development

```bash
pip install -r requirements.txt
pytest                                   # run the test suite
python scripts/build_snapshot.py         # regenerate the offline snapshot
python scripts/build_baseline.py         # regenerate the frozen baseline
```

The bundled `snapshot.json` holds **real** group-stage results curated from the
official/Wikipedia group pages, **frozen at `fetched_at`** — it exists so the
tool and tests run with no key or network. Because it is frozen it goes stale;
`scripts/build_snapshot.py` refreshes it, and live providers override it
entirely with current data.

## License

MIT — see [LICENSE](LICENSE).
