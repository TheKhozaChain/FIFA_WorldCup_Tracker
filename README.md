# wctracker — live WC2026 advancement tracker

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
        WC2026 Advancement Tracker — Group C
┏━━━━━━━━━━━┳━━━━━┳━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Team      ┃ Grp ┃ Pos ┃  Start ┃    Now ┃       Δ ┃
┡━━━━━━━━━━━╇━━━━━╇━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ Qatar     │  C  │  2  │  34.1% │ 100.0% │ ▲ +65.9 │
│ Argentina │  C  │  1  │  96.6% │ 100.0% │ ▲  +3.4 │
│ Sweden    │  C  │  3  │  57.5% │  25.5% │ ▼ -32.0 │
│ Mexico    │  C  │  4  │  75.9% │  29.6% │ ▼ -46.3 │
└───────────┴─────┴─────┴────────┴────────┴─────────┘
```

## Quick start

```bash
git clone <your-repo-url> && cd FIFA_WorldCup_2026
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Runs immediately with the bundled offline snapshot — no API key needed:
python -m wctracker --provider offline
```

To pull **live** results, get a free key and add it to `.env`:

```bash
cp .env.example .env          # then edit .env and paste your key
python -m wctracker           # uses football-data.org by default
python -m wctracker --refresh # force a fresh fetch (ignore the cache)
```

If a live fetch fails (missing key, rate limit, network), the tool falls back to
the bundled snapshot so it always prints something.

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

Every run also writes **`latest.md`** — the same table in markdown, ready to
share or commit.

## Data source

The data layer sits behind a small `DataProvider` interface
(`wctracker/providers/base.py`), so switching providers is a one-file change.

| Provider | Free tier | Coverage | Auth | Role |
| --- | --- | --- | --- | --- |
| **football-data.org** | 10 req/min | One call returns every group fixture + score, with group labels | `X-Auth-Token` header | **Default** |
| API-Football (api-sports.io) | 100 req/day | Very broad | API key header | Easy to add as another provider |
| TheSportsDB | loose, test key `3` | Variable; weaker live standings | key in URL | Bundled fallback example |
| _offline_ | — | Bundled illustrative snapshot | none | Zero-setup demo + tests |

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

The bundled `snapshot.json` is **illustrative sample data**, not official FIFA
results — it exists so the tool and tests run with no key or network. Live
providers override it entirely.

## License

MIT — see [LICENSE](LICENSE).
