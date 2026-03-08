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

ENTRYPOINT ["python", "-m", "modules.orchestrator"]
