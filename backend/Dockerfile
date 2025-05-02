FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code and database
COPY ../api2.py .
COPY ../beers.db .

# Set environment variable for the port
ENV PORT=8080

# Run the API
CMD ["python", "api2.py"]
