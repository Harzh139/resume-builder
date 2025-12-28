# Discord ATS Resume Optimizer Bot

This bot accepts a resume file via `/optimize-resume`, extracts the resume text, and forwards it to an n8n webhook for further processing.

Setup

1. Create a virtual environment and activate it.

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `DISCORD_TOKEN` and `N8N_WEBHOOK_URL`.

4. Run the bot:

```bash
python src\bot.py
```

Notes

- The bot extracts text from PDFs and DOCX when possible. Install the dependencies listed in `requirements.txt`.
- Do not commit your actual `.env` file containing secrets.

## Docker deployment

Build the Docker image and run with docker-compose (recommended):

1. Ensure you have a `.env` file in the project root containing `DISCORD_TOKEN` and `N8N_WEBHOOK_URL`.

2. Build and start:

```bash
docker-compose up -d --build
```

3. Check logs:

```bash
docker-compose logs -f
```

To stop:

```bash
docker-compose down
```

Notes:
- The `Dockerfile` installs the Python dependencies from `requirements.txt` and runs `python src/bot.py`.
- Do not commit your `.env` file to git.
