FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# Prueft, ob listen/poll noch aktiv einen Schleifendurchlauf macht (siehe
# imap_client.py, HEARTBEAT_PATH) - erkennt einen haengenden Prozess, den
# "restart: unless-stopped" allein nicht abfaengt (der greift nur bei einem
# tatsaechlichen Absturz/Exit). start-period deckt Verbindungsaufbau plus
# eine erste IDLE-Wartezeit ab.
HEALTHCHECK --interval=60s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import pathlib, sys, time; p = pathlib.Path('/tmp/agent-email-heartbeat'); sys.exit(0 if p.exists() and time.time() - p.stat().st_mtime < 180 else 1)"

CMD ["python", "main.py", "listen"]
