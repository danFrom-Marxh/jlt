FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=10000

WORKDIR /app

RUN addgroup --system django && adduser --system --ingroup django django

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY . .

# WhiteNoise sert ces fichiers directement depuis l'image.
RUN python manage.py collectstatic --noinput

RUN chmod +x /app/docker-entrypoint.sh && chown -R django:django /app
USER django

EXPOSE 10000

CMD ["/app/docker-entrypoint.sh"]
