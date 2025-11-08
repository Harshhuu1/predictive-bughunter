# Predictive Bug Hunter - MVP

## Quickstart (local)
1. Create and activate a virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start demo service:
   ```bash
   uvicorn app.main:app --port 8000
   ```
3. Start healer agent:
   ```bash
   uvicorn agents.healer_agent:app --port 9002 --reload
   ```
4. Start monitor:
   ```bash
   python agents/monitor_agent.py
   ```
5. Start predictor:
   ```bash
   python agents/predictor_agent.py
   ```

The monitor will collect metrics into `agents.db`. Predictor will analyze and send prediction events to healer, which will run a safe restart command in demo mode.
