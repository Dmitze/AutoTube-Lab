FROM python:3.11-slim

WORKDIR /app

# Install build tools
RUN pip install --upgrade pip

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY modules/ ./modules/

# Install production dependencies
RUN pip install -e .

RUN addgroup --system --gid 1001 ytaimbot \
 && adduser  --system --uid 1001 --ingroup ytaimbot --no-create-home ytaimbot \
 && mkdir -p /data \
 && chown -R ytaimbot:ytaimbot /app /data
USER ytaimbot

ENTRYPOINT ["python", "-m", "modules.orchestrator"]
