# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy your script into the container
COPY scraper.py .

# Install dependencies (e.g., requests)
RUN pip install requests

# Default command to run your script
CMD ["python", "scraper.py"]
