FROM python:3.10-slim
WORKDIR /app

COPY scaffold/markdown_kb/vendor/ /usr/local/lib/python3.10/site-packages/
COPY scaffold/markdown_kb/app/ ./app/
COPY scaffold/markdown_kb/chat.html .
COPY docs/ ./docs/

ENV KB_ROOT=/app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
