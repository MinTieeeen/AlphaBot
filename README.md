# AlphaBot - OptiSigns Support Assistant

Lightweight chatbot that answers questions about OptiSigns using RAG (Retrieval-Augmented Generation).

## Quick Start

```bash
# 1. Clone & install
git clone <your-repo>
cd alphabot
pip install -r requirements.txt

# 2. Configure
cp .env.sample .env
# Edit .env and add your OPENAI_API_KEY

# 3. Run scraper (downloads articles)
python main.py --scrape

# 4. Upload to vector store
python main.py --upload

# 5. Verify
python main.py --test "How do I add a YouTube video?"
```

## Docker

```bash
docker build -t alphabot .
docker run -e OPENAI_API_KEY=sk-xxx alphabot
```

## Architecture

- `main.py` - Orchestrates scrape → upload workflow
- `scraper.py` - Downloads articles from OptiSigns support
- `uploader.py` - Uploads markdown to OpenAI Vector Store
- `content/` - Cached markdown files

## Daily Job

Deployed on Railway/Render with daily cron trigger.
Job logs: [Link to deployment logs]

## Screenshot

![Assistant Demo](screenshot.png)
