# 🛡️ SAAB STRATEGIC MISSION PROTOCOL

This document defines the mandatory operational readiness steps required before any tactical simulation or dashboard analysis is performed. 

> [!IMPORTANT]
> **MANDATORY PRE-FLIGHT CHECKLIST**
> Before executing any browser subagent or scratchpad logic, you MUST verify the following:
> 1. **Neural Backend**: Ensure `agent_backend.py` is running on `http://localhost:8000`.
> 2. **Tactical Frontend**: Ensure the HTTP server is running on `http://localhost:8080`.
> 3. **Theater Sync**: Verify that the 21-point Boreal dataset is loaded in all active views.

## 🚀 SERVER LAUNCH COMMANDS
If servers are down, execute the following in order:

```powershell
# 1. Start Backend
C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe src\agent_backend.py

# 2. Start Frontend
C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe -m http.server 8080
```

## 🧠 NEURAL CORE PROFILES
| Model | Logic Profile | Tactical Pk | Key Feature |
| :--- | :--- | :--- | :--- |
| **Elite V3.5** | Direct Action | 98% | Max Kinetic Accuracy |
| **Hybrid RL** | Hungarian | 95% | Strategic Efficiency |
| **Titan** | Multi-Vector | 92% | Saturated Wave Handling |
| **Heuristic** | Triage-Aware | 74.5% | Reliable Rule Baseline |

## 📍 THEATER GRID (21 POINTS)
Ensure all 12 Location Nodes and 9 Terrain Nodes are rendered on the Strategic Map.

---
**STATUS: MISSION READY**
*Protocol Version: 1.0.0*
