# Day 7-8: Containerization
# Lets the pipeline run identically on any machine (your laptop, GitHub Actions, anywhere)
# without needing Python or dependencies installed locally.

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (separate layer = faster rebuilds when only code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual source code
COPY src/ ./src/

# NEON_DATABASE_URL and GEMINI_API_KEY are passed in at runtime via --env-file or -e flags,
# never baked into the image.

CMD ["python", "src/pipeline.py"]