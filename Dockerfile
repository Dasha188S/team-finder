FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системные зависимости: компиляция psycopg2-binary не нужна, но libpq и шрифт
# для генерации аватаров (Pillow) — желательны.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# entrypoint: ждёт БД, мигрирует, собирает статику, запускает gunicorn
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "team_finder.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
