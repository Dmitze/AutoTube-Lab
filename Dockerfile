FROM python:3.11-slim

WORKDIR /app

# 1. System dependencies: ffmpeg (video assembly T-170, T-080) + curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip
RUN pip install --upgrade pip

# 3. Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY modules/ ./modules/

# 4. Install Python dependencies (includes trendspy, google-api-python-client, groq, edge-tts)
RUN pip install -e .

# 5. Create non-root user and set permissions
RUN addgroup --system --gid 1001 ytaimbot \
 && adduser  --system --uid 1001 --ingroup ytaimbot --no-create-home ytaimbot \
 && mkdir -p /data \
 && chown -R ytaimbot:ytaimbot /app /data

# Switch to non-root user for security
USER ytaimbot

ENTRYPOINT ["python", "-m", "modules.orchestrator"]