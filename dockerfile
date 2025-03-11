# Etapa Base
FROM python:3.10 AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Etapa Final
FROM base AS final

WORKDIR /app

COPY . .

RUN mkdir -p /app/staticfiles /app/media

# Coletar arquivos estáticos antes de iniciar o servidor
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "/app", "core.wsgi:application", "--workers", "3", "--timeout", "120", "--preload"]
