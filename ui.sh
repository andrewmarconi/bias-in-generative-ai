#!/bin/bash

echo "Loading MLFlow UI..."
uv run mlflow ui \
    --backend-store-uri sqlite:///mlflow.db \
    --host 0.0.0.0 \
    --port 5001
