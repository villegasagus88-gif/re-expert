FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Railway sets $PORT dynamically; fallback to 8000 for local dev.
# --proxy-headers + --forwarded-allow-ips='*' make Starlette honor the
# X-Forwarded-Proto / X-Forwarded-For headers set by Railway's edge proxy,
# so request.url.scheme reflects the real client scheme (https) and
# HTTPSRedirectMiddleware does NOT bounce healthy HTTPS requests.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'
