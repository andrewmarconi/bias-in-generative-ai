#!/usr/bin/env bash
set -euo pipefail

# WARNING: This will permanently remove local MLflow data (mlruns and mlflow.db)

ROOT_DIR=$(git rev-parse --show-toplevel)
MLRUNS_DIR="$ROOT_DIR/mlruns" 
MLFLOW_DB="$ROOT_DIR/mlflow.db"

if [ -d "$MLRUNS_DIR" ]; then
  echo "Removing MLflow runs directory: $MLRUNS_DIR"
  rm -rf "$MLRUNS_DIR"
else
  echo "MLflow runs directory not found: $MLRUNS_DIR"
fi

if [ -f "$MLFLOW_DB" ]; then
  echo "Removing MLflow tracking DB: $MLFLOW_DB"
  rm -f "$MLFLOW_DB"
else
  echo "MLflow DB not found: $MLFLOW_DB"
fi

echo "MLflow store reset complete."