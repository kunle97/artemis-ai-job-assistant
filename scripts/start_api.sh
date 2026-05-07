#!/bin/bash
# Script to activate Python virtual environment and start API

set -e

cd services/api
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "No virtual environment found in services/api (.venv or venv)"
    exit 1
fi

uvicorn src.main:app --reload
