#!/bin/bash

echo "==========================================="
echo "  Starting Boreal Chessmaster Environment  "
echo "==========================================="

# 1. Spin up the backend and frontend containers
echo "[1/3] Building and starting Docker containers..."
docker-compose up --build -d

# 2. Give the FastAPI server a few seconds to fully initialize
echo "[2/3] Waiting for the Boreal Chessmaster API to boot up..."
sleep 5

# 3. Run the batch testing script
echo "[3/3] Initiating automated batch tests..."
python src/batch_tester.py

echo ""
echo "==========================================="
echo "  Batch Testing Complete!                  "
echo "  Tactical Dashboard is now live at:       "
echo "  http://localhost:8080                    "
echo "==========================================="