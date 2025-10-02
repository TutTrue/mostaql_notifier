#!/bin/bash

# This script is called by cron to run the Mostaql notifier
# It ensures the environment variable is properly passed

# Read the environment variable from a file that was written by the entrypoint
if [ -f "/app/.env_vars" ]; then
    source /app/.env_vars
fi

# Run the script as the mostaql user with the environment variable
su - mostaql -c "cd /app && MOSTAQLWEB='$MOSTAQLWEB' /usr/local/bin/python main.py"
