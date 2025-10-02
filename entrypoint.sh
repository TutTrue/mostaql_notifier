#!/bin/bash

# Start cron service
echo "Starting cron service..."
service cron start

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Run the script once immediately as mostaql user
echo "$(date): Starting Mostaql notifier..." >> /app/logs/mostaql.log
su - mostaql -c "cd /app && MOSTAQLWEB='$MOSTAQLWEB' python main.py" >> /app/logs/mostaql.log 2>&1

# Keep the container running and show logs
echo "$(date): Mostaql notifier started. Running every 1 minute..." >> /app/logs/mostaql.log
echo "Logs will be written to /app/logs/mostaql.log"
echo "You can view logs with: docker logs <container_name>"

# Tail the log file to keep container running and show output
tail -f /app/logs/mostaql.log

