# ViralScope Engine

Automated viral content trend intelligence engine for the ViralScope Flutter mobile app.

Scrapes public trend signals from multiple sources, analyzes them with AI, scores creator opportunities, and exports JSON feeds consumed via GitHub RAW URLs — no backend server required.

## Features

- **7 isolated scrapers** — Google Trends, YouTube, Reddit, TikTok, AI creator trends, Shorts/Reels niches, emerging topics
- **AI enrichment** — OpenAI-powered hooks, hashtags, thumbnail text, and creator insights
- **Scoring engine** — Trading-signal-style viral probability, saturation risk, and opportunity scores
- **Tiered JSON exports** — `free.json`, `premium.json`, `trends.json`
- **Automated scheduling** — Runs every 6 hours with retry logic and structured logging
- **No backend required** — Static JSON files hosted on GitHub for Flutter consumption

## Architecture

```
ViralScope Engine/
├── sources/          # Isolated scraper modules
├── analyzers/        # Scoring engine + OpenAI analyzer
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
Scrape (async) → Deduplicate → Score → AI Enrich → Export JSON
```

## Requirements

- Python 3.12+
- OpenAI API key (optional — fallback analysis available)

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd "ViralScope Engine"

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key for AI analysis |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `AI_ANALYSIS_ENABLED` | `true` | Enable/disable AI enrichment |
| `SCHEDULE_INTERVAL_HOURS` | `6` | Automation interval |
| `FREE_TREND_LIMIT` | `3` | Trends in free tier export |
| `GOOGLE_TRENDS_GEO` | `US` | Google Trends region |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

See `.env.example` for all available options.

## Usage

### Run Once

Execute the full pipeline immediately:

```bash
python main.py run
```

### Start Scheduler (Production)

Run as a daemon, executing every 6 hours:

```bash
python main.py schedule
```

### Generate Sample Exports

Create demo JSON files without scraping:

```bash
python main.py export-sample
```

## JSON Exports

All exports are written to `/exports`:

### `free.json` — Free App Tier

- First 3 trends only
- Limited fields: id, title, category, description, viral_score, growth_velocity, best_platform, created_at
- No AI analysis, hooks, or hashtags

### `premium.json` — PRO App Tier

- All trends with full data
- AI analysis, hook ideas, thumbnail text, hashtags, creator insights

### `trends.json` — Master Export

- Complete raw trend data including source metadata and signal data
- Used for debugging and analytics

### Example Trend Object (Premium)

```json
{
  "id": "a1b2c3d4-...",
  "title": "AI Avatar Story Channels",
  "category": "Creator",
  "description": "Faceless AI-generated narrative channels exploding on YouTube Shorts",
  "viral_score": 94,
  "confidence_score": 89,
  "growth_velocity": "Extreme",
  "competition_level": "Low",
  "saturation_risk": "Low",
  "best_platform": "YouTube Shorts",
  "thumbnail_text": "AI STORIES GO VIRAL",
  "hashtags": ["#AIStories", "#FacelessYouTube", "#Shorts"],
  "hook_ideas": ["This AI channel got 1M views in 30 days"],
  "ai_analysis": "AI avatar storytelling represents an extreme-growth opportunity...",
  "creator_insights": ["Launch within 2 weeks before saturation increases"],
  "created_at": "2026-05-21T12:00:00+00:00"
}
```

## Flutter Integration

Host exports on GitHub and consume via RAW URLs:

```
https://raw.githubusercontent.com/<user>/<repo>/main/exports/free.json
https://raw.githubusercontent.com/<user>/<repo>/main/exports/premium.json
```

Automate updates with GitHub Actions (run engine → commit exports → push).

## Scraping Sources

All scrapers use **public-safe methods only**:

| Source | Method | Data |
|---|---|---|
| Google Trends | Public RSS feed | Daily trending searches |
| YouTube | Public RSS feeds | Trending channel videos |
| Reddit | Public `.json` endpoints | Hot posts from creator subreddits |
| TikTok | Public discovery pages | Trend hashtags and niches |
| AI Creator Trends | Public RSS (HN) + curated signals | AI/tech creator topics |
| Shorts/Reels | Reddit search + curated niches | Short-form viral niches |
| Emerging Topics | Public RSS + curated signals | Early-stage creator opportunities |

## Automation with GitHub Actions

Create `.github/workflows/viralscope.yml`:

```yaml
name: ViralScope Engine
on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

jobs:
  run-engine:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python main.py run
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: update trend exports"
          file_pattern: exports/*.json
```

## Scoring Engine

Inspired by betting tips and trading signal apps:

| Metric | Range | Description |
|---|---|---|
| `viral_score` | 10–99 | Overall viral probability |
| `confidence_score` | 20–99 | Signal confidence level |
| `growth_velocity` | Extreme → Stagnant | Trend momentum |
| `competition_level` | Very Low → Very High | Creator competition |
| `saturation_risk` | Very Low → Very High | Market saturation |

## Logging

Structured logs are saved to `/logs`:

- `viralscope_YYYY-MM-DD.log` — All log levels
- `errors_YYYY-MM-DD.log` — Errors only

Logs rotate at 10 MB with 30-day retention.

## Development

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py run

# Generate sample data for Flutter development
python main.py export-sample
```

## License

Proprietary — ViralScope
