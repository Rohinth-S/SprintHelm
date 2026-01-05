# Production Dockerfile for CodinzHub Sprint Guardian
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy source code and configurations
COPY . .

# Run validator to verify container configuration
RUN python automation/codinzhub-validate-skill.py

# Expose default entrypoint
ENTRYPOINT ["python", "-m", "sprint_guardian"]
CMD ["--mode", "standup-brief"]
