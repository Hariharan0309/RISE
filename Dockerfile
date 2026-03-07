FROM python:3.12-slim

# 1. Python environment variables for container optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 2. Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . .

# 5. Expose port 8080 (AWS App Runner's default port)
EXPOSE 8080

# 6. Streamlit configuration via Environment Variables
# This avoids config.toml formatting errors and guarantees Streamlit reads them
ENV STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 7. Start the application
CMD ["streamlit", "run", "app.py"]