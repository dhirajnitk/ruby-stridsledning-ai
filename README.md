# Boreal Chessmaster: Tactical Air Defense AI

The Boreal Chessmaster is an advanced, AI-driven tactical air defense engine designed to assist combat controllers (*Stridsledare*) by evaluating threats, mathematically optimizing interceptor assignments using the Hungarian Algorithm, and probabilistically simulating futures using Monte Carlo Tree Search (MCTS).

## 🚀 Getting Started

You can run the Boreal Chessmaster either natively on your local machine or using Docker for a fully containerized environment.

**Note on Reinforcement Learning (RL):** The codebase contains advanced RL training scripts (`train_value_network.py`, `train_doctrine_manager.py`, etc.) for an AlphaZero-style architecture. For ease of setup and evaluation, **the RL engine is disabled by default for the time being**. The engine is designed to gracefully fall back to the classical MCTS physics engine automatically if PyTorch models are not found in the directory.

---

## Option 1: Running Without Docker (Local Setup)

### 💻 Windows Quick Start (Automated)
For Windows users, we have provided an automated PowerShell script that handles everything. It creates an isolated virtual environment (`.venv_saab`), installs all dependencies, sets the OpenRouter API key, and boots up both servers simultaneously.
```powershell
# Open PowerShell in the project directory and run:
.\run_local_windows.ps1
```
*(Note: If script execution is blocked by your system, you may need to run `Set-ExecutionPolicy Bypass -Scope Process` first).*

### 🐧 Manual Setup (Linux / Mac / Advanced)
If you are on Linux/Mac or prefer to set up the environment manually:

### Prerequisites
* Python 3.10+
* A modern web browser

### 1. Create Virtual Environment & Install Dependencies
Open a terminal in the project directory, create a virtual environment, and install the required packages.
```bash
python -m venv .venv_saab
source .venv_saab/bin/activate  # On Windows use: .\.venv_saab\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional)
To enable the Gemini LLM SITREP generation, set your OpenRouter API key:
*   **Windows (Command Prompt):** `set OPENROUTER_API_KEY=your_key_here`
*   **Windows (PowerShell):** `$env:OPENROUTER_API_KEY="your_key_here"`
*   **Linux/Mac:** `export OPENROUTER_API_KEY="your_key_here"`

### 3. Start the Backend Server
```bash
# Ensure you run this from the root directory so Python pathing works
python src/agent_backend.py
```
The FastAPI server will start on `http://localhost:8000`.

Simply open `frontend/index.html` directly in your web browser, or run a lightweight local Python web server from the root directory:
```bash
python -m http.server 8080 --directory frontend
```
Then navigate to `http://localhost:8080` in your browser.

---

## Option 2: Running With Docker (Recommended)

If you have Docker and Docker Compose installed, you can spin up the entire stack (Backend + Frontend Nginx server) with a single command.

### 1. Using the Automated Script
We have provided a bash script that builds the containers, waits for the backend to initialize, and automatically kicks off the headless batch testing suite.
```bash
# Make the script executable (Linux/Mac/Git Bash on Windows)
chmod +x run_all.sh

# Run the stack
./run_all.sh
```
The Tactical Dashboard will be live at `http://localhost:8080`.

### 2. Manual Docker Compose
Alternatively, you can manually spin up the environment in the background:
```bash
docker-compose up --build -d
```

---

---

## 📡 How It Works: The Radar & Data Flow

When running the Boreal Chessmaster interactively, you might wonder: **How does the frontend get data about enemy aircraft and missiles?**

1. **Local Simulation (The Radar):** In this interactive prototype, the frontend (`index.html`) acts as the radar simulator. When you click **"Spawn Radar Threat"**, the browser's JavaScript natively generates a hostile unit (e.g., a Decoy, Bomber, or Hypersonic) with specific coordinates, speeds, and headings.
2. **The API Payload:** The frontend constantly scans its local canvas. It packages all visible, non-triaged threats into a JSON array and sends it to the Python Backend via an HTTP `POST` request to `/api/evaluate-threats`.
3. **The AI Brain (Backend):** The FastAPI backend receives this "radar frame". It runs the heavy mathematics (Hungarian Algorithm + Monte Carlo Tree Search), asks the LLM to write a Situation Report (SITREP), and replies with a JSON list of optimal tactical assignments.
4. **Execution:** The frontend receives these tactical assignments, deducts the fired weapons from the UI ammo counters, and draws the intercept lines and explosions on the screen.

### 🖱️ Does "Spawn Radar Threat" work continuously?
In the interactive dashboard, the **"Spawn Radar Threat"** button is a manual action. 
* **Manual Spawning:** Each click generates exactly one random enemy unit (like a Decoy or Bomber) at the edge of the map. To simulate a massive swarm, you must click rapidly!
* **Continuous Movement:** Once spawned, the internal physics loop takes over and moves the threats continuously toward your bases.
* **Continuous AI Evaluation:** With the **"Auto-Poll AI"** checkbox ticked, the frontend automatically sends the current radar state to the backend every 3 seconds to get fresh tactical orders.
*(Note: For complex, continuous waves of enemies that spawn automatically over time, use the headless **Batch Tester**.)*

---

## 🧪 Automated Testing & AI Optimization

Beyond the interactive dashboard, Boreal Chessmaster includes a headless simulation suite designed to mathematically prove the engine's robustness.

### The Batch Tester (`src/batch_tester.py`)
This script rigorously stress-tests the AI engine against 100 highly complex, LLM-generated adversarial scenarios from `data/input/` without requiring the frontend UI.
```bash
python src/batch_tester.py
```
*This will output a live terminal table of the evaluations, export a `.csv` report to `data/results/`, and generate a high-resolution performance trend chart (`.png`).*

---

## 📁 Repository Structure
Following the latest restructuring, the project is highly modular:
*   `src/`: Core Python source code (`agent_backend.py`, `engine.py`, `batch_tester.py`, RL scripts).
*   `data/input/`: Static map coordinates (`Boreal_passage_coordinates.csv`) and Red Team JSON scenarios.
*   `data/results/`: Output directories for generated charts and performance metrics.
*   `docs/`: Extensive architectural documentation and the original Saab Hackathon criteria PDF.
*   `frontend/`: The interactive HTML5/Canvas UI (`index.html`).
