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
