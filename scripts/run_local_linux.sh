#!/bin/bash
# Boreal Chessmaster - Linux/macOS Local Environment Launcher
# 🛡️ SAAB HACKATHON 2026 - FINAL MISSION PROTOCOL

echo -e "\e[36m========================================="
echo -e "   Starting Boreal Command Suite (Local) "
echo -e "   NATO/Sweden Doctrine: SYNCHRONIZED    "
echo -e "=========================================\e[0m"

# 1. Environment Configuration
echo -e "\n\e[33m[1/5] Setting Environment Variables...\e[0m"
export PYTHONPATH="./.local_lib"
export SAAB_MODE="sweden"
export OPENROUTER_API_KEY="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"
echo -e "\e[32mPYTHONPATH set to .local_lib (DLL Resolution Active).\e[0m"

# 2. Python Check
echo -e "\n\e[33m[2/5] Checking Python installation...\e[0m"
if ! command -v python3 &> /dev/null; then
    echo -e "\e[31mERROR: python3 is not installed.\e[0m"; exit
fi
python3 --version

# 3. Virtual Environment
echo -e "\n\e[33m[3/5] Syncing Dependencies (Parent Venv)...\e[0m"
VENV_PATH="../.venv_saab"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\e[36mCreating venv in parent...\e[0m"
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"
pip install -r requirements.txt

# 4. Start Backend
echo -e "\n\e[33m[4/5] Launching Tactical Engine Backend...\e[0m"
python3 src/agent_backend.py &
BACKEND_PID=$!
echo -e "\e[32mBackend initializing (PID: $BACKEND_PID) on http://localhost:8000...\e[0m"
sleep 5

# 5. Start Frontend
echo -e "\n\e[33m[5/5] Opening Tactical Dashboard...\e[0m"
python3 -m http.server 8080 &
FRONTEND_PID=$!
sleep 2

# Attempt to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080/dashboard.html"
elif command -v open &> /dev/null; then
    open "http://localhost:8080/dashboard.html"
fi

echo -e "\n\e[32m[SUCCESS] BOREAL COMMAND SUITE IS LIVE!\e[0m"
echo -e "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo -e "Press Ctrl+C to shut down both servers.\n"

# Trap SIGINT to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT
wait
