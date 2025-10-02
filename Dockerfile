FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    beep \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
# COPY test_with_file.py .
# COPY mostaql.html .

# Copy entrypoint script and make it executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy cron runner script and make it executable
COPY run_cron.sh .
RUN chmod +x run_cron.sh

# Create a non-root user
RUN useradd -m -u 1000 mostaql && chown -R mostaql:mostaql /app

# Create logs directory
RUN mkdir -p /app/logs && chown mostaql:mostaql /app/logs

# Set up cron job to run every 1 minute (as root, but execute as mostaql user)
# The environment variable will be passed from the entrypoint script
RUN echo "*/1 * * * * /app/run_cron.sh >> /app/logs/mostaql.log 2>&1" | crontab -

# Keep running as root for cron to work
# USER mostaql

# Expose port (optional, for health checks)
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]

