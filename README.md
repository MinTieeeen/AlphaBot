# AlphaBot - OptiSigns Support Assistant

RAG-based chatbot that answers questions about OptiSigns using your uploaded documentation.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.sample .env
# Add your OPENAI_API_KEY to .env

# Run scraper (downloads articles)
python main.py --scrape

# Upload to vector store
python main.py --upload

# Test the assistant
python main.py --test "How do I add a YouTube video?"
```

## Docker

```bash
# Build
docker build -t alphabot .

# Run (one-shot, exits after completion)
docker run -e OPENAI_API_KEY=sk-xxx alphabot
```

## Deployment (Railway)

1. Fork/clone this repo to GitHub
2. Create account at [railway.app](https://railway.app)
3. New Project → Deploy from GitHub repo
4. Add Environment Variable: `OPENAI_API_KEY`
5. Add Persistent Disk (for content/)
6. Set up Cron Job:
   - Project Settings → Triggers → New Trigger
   - Schedule: `@daily` or `0 0 * * *`
   - Command: `python main.py --scrape --upload`

## Architecture

| File | Purpose |
|------|---------|
| `main.py` | Entry point, orchestrates workflow |
| `scraper.py` | Fetches articles via Zendesk API |
| `uploader.py` | Uploads MD to OpenAI Vector Store |
| `assistant.py` | Tests chatbot via API |
| `content/` | Cached markdown files |

## Chunking Strategy

Files are split by paragraphs (double newlines), combined until 1000 chars, with 200 char overlap. This preserves semantic context while keeping chunks manageable.

## Logs

Job execution logs available in Railway dashboard under Deployments → Logs.

## Screenshot

![Assistant Demo](screenshot.png)
