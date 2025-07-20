FROM python:3.10-slim

WORKDIR /app
COPY scraper.py .

RUN pip install requests

CMD ["python", "scraper.py"]
