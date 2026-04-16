#!/usr/bin/env bash

set -euo pipefail

# Minimal helper script for the first local demo.
# This script does not start a full platform stack yet. It only prints the
# recommended sequence to run the mock API and Streamlit dashboard.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "MetricForge NYC local demo"
echo
echo "1. Create and activate a virtual environment"
echo "   cd \"${PROJECT_ROOT}\""
echo "   python3 -m venv .venv"
echo "   source .venv/bin/activate"
echo
echo "2. Install dependencies"
echo "   pip install -r requirements.txt"
echo
echo "3. Ensure MinIO contains the raw source files"
echo "   bash scripts/download_nyc_taxi_data.sh"
echo
echo "4. Start the API"
echo "   uvicorn api.main:app --reload"
echo
echo "5. In another terminal, start the dashboard"
echo "   streamlit run dashboard/app.py"
