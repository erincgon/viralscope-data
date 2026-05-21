# ViralScope Engine

Automated viral content trend intelligence engine for the ViralScope Flutter mobile app.

Scrapes **public, free** trend signals from multiple sources, scores creator opportunities with a rule-based engine, generates hooks and hashtags from templates, and exports JSON feeds consumed via GitHub RAW URLs — **no backend server, no paid APIs, no OpenAI**.

## Features

- **7 isolated scrapers** — Google Trends, YouTube, Reddit, TikTok, creator economy, Shorts/Reels niches, emerging topics
- **Rule-based intelligence** — Template hooks, hashtags, thumbnail text, and creator insights (zero AI API cost)
- **Multi-signal scoring** — Trading-signal-style viral score, confidence, growth velocity, competition, saturation
- **Tiered JSON exports** — `free.json`, `premium.json`, `trends.json`
- **GitHub Actions ready** — Fast, low-memory pipeline with retry logic and graceful scraper failures
- **No backend required** — Static JSON files hosted on GitHub for Flutter consumption

## Architecture

```
ViralScope Engine/
├── sources/          # Isolated scraper modules
├── analyzers/        # Scoring engine + content generator
├── exporters/        # Centralized JSON export
├── models/           # Domain models (Trend)
├── config/           # Centralized settings
├── utils/            # HTTP client, logging, retry
├── exports/          # Generated JSON output
├── logs/             # Structured log files
└── main.py           # Pipeline orchestrator
```

### Pipeline Flow

```
Scrape (async) → Deduplicate & merge signals → Score → Enrich content → Export JSON
```

## Requirements

- Python 3.12+
- **No API keys required** for core operation
- Optional: Reddit API credentials (free) for PRAW-enhanced scraping

## Installation

```bash
git clone <your-repo-url>
cd viralscope-data

python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Optional `.env` (copy from `.env.example`) — all variables have safe defaults.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SCHEDULE_INTERVAL_HOURS` | `6` | Automation interval |
| `FREE_TREND_LIMIT` | `3` | Trends in free tier export |
| `GOOGLE_TRENDS_GEO` | `US` | Google Trends region |
| `USE_PYTRENDS` | `true` | Supplement RSS with pytrends |
| `REDDIT_CLIENT_ID` | — | Optional free Reddit API (PRAW) |
| `REDDIT_CLIENT_SECRET` | — | Optional Reddit API secret |
| `CONCURRENT_REQUESTS` | `4` | Scraper concurrency (CI-friendly) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Usage

### Run Once

```bash
python main.py run
```

### Start Scheduler (Production)

```bash
python main.py schedule
```

### Generate Sample Exports

```bash
python main.py export-sample
```

## JSON Exports

All exports are written to `exports/`:

### `free.json` — Free App Tier

- First 3 trends only
- Lightweight fields: id, title, category, description, viral_score, growth_velocity, best_platform, created_at

### `premium.json` — PRO App Tier

- All trends with full data
- Hooks, hashtags, thumbnail text, creator insights, trend analysis summary

### `trends.json` — Master Export

- Complete raw trend data including `raw_signals` and source metadata

### Example Scoring (Premium)

```json
{
  "viral_score": 94,
  "confidence_score": 89,
  "growth_velocity": "Extreme",
  "competition_level": "Low",
  "saturation_risk": "Low",
  "best_platform": "YouTube Shorts"
}
```

## Flutter Integration

```
https://raw.githubusercontent.com/<user>/<repo>/main/exports/free.json
https://raw.githubusercontent.com/<user>/<repo>/main/exports/premium.json
```

Automate with GitHub Actions (included workflow commits exports on each run).

## Scraping Sources

All scrapers use **public-safe methods only**:

| Source | Method | Data |
|---|---|---|
| Google Trends | Public RSS + optional pytrends | Daily trending searches |
| YouTube | Public RSS feeds | Trending channel videos |
| Reddit | Public `.json` or optional PRAW | Hot posts from creator subreddits |
| TikTok | Public discovery / Creative Center | Hashtag and niche signals |
| Creator Economy | Public RSS (HN) + curated | Tech/creator topics |
| Shorts/Reels | Reddit search + curated niches | Short-form viral niches |
| Emerging Topics | Public RSS + curated | Early-stage opportunities |

## GitHub Actions

Workflow: `.github/workflows/viralscope.yml`

- Runs every 6 hours (or on manual dispatch)
- No secrets required
- Commits updated `exports/*.json` automatically

## Scoring Engine

Inspired by betting tips and trading signal apps:

| Metric | Range | Description |
|---|---|---|
| `viral_score` | 10–99 | Overall viral probability |
| `confidence_score` | 20–99 | Multi-signal confidence |
| `growth_velocity` | Extreme → Stagnant | Trend momentum |
| `competition_level` | Very Low → Very High | Creator competition |
| `saturation_risk` | Very Low → Very High | Market saturation |

Signals include keyword popularity, Reddit engagement, YouTube feed position, Google rank, and TikTok hashtag strength.

## Logging

Structured logs in `logs/`:

- `viralscope_YYYY-MM-DD.log` — All levels
- `errors_YYYY-MM-DD.log` — Errors only

## Development

```bash
LOG_LEVEL=DEBUG python main.py run
python main.py export-sample
```

## License

Proprietary — ViralScope
