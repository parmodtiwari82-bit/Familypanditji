FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    JPL_EPHEMERIS_PATH=/app/backend/data/ephemeris/de440s.bsp

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
COPY backend/requirements-astronomy.txt /app/backend/requirements-astronomy.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install --no-cache-dir -r /app/backend/requirements-astronomy.txt \
    && useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser . /app

# Bundle the freely available NASA/JPL DE440s data so "auto" selects the
# Skyfield/JPL astronomy engine in this image instead of silently falling
# back to the low-precision dependency-free approximation.
RUN mkdir -p /app/backend/data/ephemeris \
    && python /app/scripts/download_ephemeris.py --directory /app/backend/data/ephemeris \
    && test -s /app/backend/data/ephemeris/de440s.bsp \
    && chown -R appuser:appuser /app/backend/data/ephemeris

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
