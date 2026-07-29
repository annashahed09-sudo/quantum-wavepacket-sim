FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the package (preferred) — falls back to requirements.txt
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "src/main.py"]
