FROM python:3.13.2-slim

# Set working directory
WORKDIR /app/src/snake/

# Install system dependencies required to build packages like bcrypt
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config /app/config
COPY src /app/src
COPY static /app/static
COPY templates /app/templates

COPY .gitignore /app/.gitignore
COPY config.json /app/config.json
COPY requirements.txt /app/requirements.txt
COPY README.md /app/README.md
COPY Dockerfile /app/Dockerfile


# Expose your desired port
EXPOSE 8004

# Run the app (note: Flask doesn't use "-p", that's probably your custom arg)
CMD ["python", "app.py", "-p", "8004"]
