FROM python:3.13-slim

# System deps (optional but useful for wheels that need build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy only dependency files first (layer caching)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# (Optional) Streamlit config via env (can override at run-time)
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    PYTHONUNBUFFERED=1

# Use non-root
USER ${USER}

# Expose port
EXPOSE 8501

# Healthcheck (simple TCP)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD /bin/sh -c "nc -z 127.0.0.1 8501 || exit 1"

# Run the app (edit the path if your main file is different)
CMD ["streamlit", "run", "app.py"]
