#!/bin/bash
set -e

echo "Generating training data..."
cd /app/models && python generate_training_data.py

echo "Training AI agents..."
cd /app/models && python train_agents.py || echo "Training completed with warnings (some agents may need more data)"

echo "Starting AI service..."
cd /app && exec uvicorn api.agent_api:app --host 0.0.0.0 --port 8001 --reload
