FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy relevant files
RUN mkdir -p logs processing/tmp src
COPY main.py .
COPY src/api_server ./src/api_server
COPY custom_apis .
COPY config.yaml .
COPY LICENSE .
COPY README.md .
RUN mkdir -p logs processing/tmp

# Expose the port
EXPOSE 43080

# Command to run the application
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "43080"]
