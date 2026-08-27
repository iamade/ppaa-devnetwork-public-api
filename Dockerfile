FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY frontend ./frontend

RUN pip install --no-cache-dir .

EXPOSE 8005

CMD ["uvicorn", "ppaa_showcase.main:app", "--host", "0.0.0.0", "--port", "8005"]
