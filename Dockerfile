FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1

EXPOSE 6031

CMD ["python", "-m", "src.main"]
