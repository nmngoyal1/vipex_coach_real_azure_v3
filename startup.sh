#!/bin/bash
set -e

echo "===== VIPEX Coach Startup ====="
echo "Current directory:"
pwd

echo "Files:"
ls -la

echo "App folder:"
ls -la app

echo "Python version before venv:"
python --version || true

if [ -d "/home/site/wwwroot/antenv" ]; then
  echo "Activating Oryx antenv"
  source /home/site/wwwroot/antenv/bin/activate
elif [ -d "/home/site/wwwroot/.python_packages" ]; then
  echo "Using .python_packages"
  export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:$PYTHONPATH"
else
  echo "No Oryx venv found"
fi

echo "Python version after venv:"
python --version

echo "Checking gunicorn:"
python -m gunicorn --version

echo "Starting FastAPI app..."
exec python -m gunicorn \
  -w 1 \
  -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  --log-level debug \
  --access-logfile - \
  --error-logfile - \
  --capture-output
