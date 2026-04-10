#!/bin/bash
set -e

echo "Running database seed..."
python seed_data.py

echo "Starting backend server..."
exec uvicorn app.main:application --host 0.0.0.0 --port 8000 --reload
