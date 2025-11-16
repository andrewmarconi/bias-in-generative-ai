#!/bin/bash

echo "Loading MLFlow UI..."
echo "Access at: http://localhost:5001"
echo "Press Ctrl+C to stop"
uv run mlflow ui --port 5001
