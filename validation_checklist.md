# Validation Checklist

This checklist captures the minimum manual validation path for the browser publisher and Python backend after steps 002 to 004.

## 1. Prerequisites

- Use Python 3.10 to 3.12 when possible.
- Install backend dependencies with `pip install -r requirements.txt`.
- Install frontend dependencies with `cd frontend && npm install`.
- Review `.env.example` and `frontend/.env.example` before changing runtime settings.

## 2. Backend Smoke Test

1. Start the backend from the repository root:

   ```bash
   source /path/to/venv/bin/activate
   python -m backend.app
   ```

2. From another terminal, run:

   ```bash
   python scripts/smoke_test_backend.py
   ```

3. Expect:

   - `Smoke test passed`
   - `GET /health` returns `200`
   - `GET /openapi.json` includes `/api/webrtc/offer`
   - Invalid `POST /api/webrtc/offer` payload returns `422`

## 3. Localhost Happy Path

1. Start the backend:

   ```bash
   python -m backend.app
   ```

2. Start the frontend:

   ```bash
   cd frontend
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

3. Open `http://127.0.0.1:5173`.
4. Click `開始送流` and allow camera permission.
5. Expect:

   - The page enters `Connected`
   - Local preview appears
   - Backend logs `Receiving video track`
   - Backend logs `Processed 1 frames` and continues counting frames

## 4. Stop and Reload Cleanup

1. While connected, click `停止送流`.
2. Expect:

   - The page returns to `Idle`
   - Local preview is cleared
   - Backend logs `Closed peer session ...`
   - `/health` shows `activePeers=0`

3. Start a new stream again, then reload the browser tab.
4. Expect:

   - Backend logs the current peer session closing
   - `/health` returns `activePeers=0`
   - The reloaded page returns to the initial idle state

## 5. Permission Denied Path

1. Block or deny browser camera access.
2. Click `開始送流`.
3. Expect:

   - The page enters `Error`
   - A permission-related error message is visible
   - No peer session remains active on the backend

## 6. Backend Unavailable Path

1. Stop the backend.
2. Keep the frontend running and open the publisher page.
3. Click `開始送流`.
4. Expect:

   - The page enters `Error`
   - The UI shows `Backend health check failed ... Verify backend.app is running and reachable.`
   - No browser offer is created

## 7. Same-LAN / Direct Backend Check

1. Start the backend with a reachable host:

   ```bash
   BACKEND_HOST=0.0.0.0 python -m backend.app
   ```

2. Add the frontend origin to `BACKEND_CORS_ALLOW_ORIGINS` if the browser will call the backend directly.
3. If frontend and backend run on different machines, set one of these:

   - `VITE_DEV_PROXY_TARGET=http://<backend-lan-ip>:8000`
   - `VITE_API_BASE_URL=http://<backend-lan-ip>:8000`

4. Expect:

   - `GET /health` succeeds from the browser
   - Offer/answer still completes on a simple same-LAN path
   - If the path crosses harder NAT or enterprise firewall boundaries, failure is expected without STUN/TURN

## 8. Known Limits

- `getUserMedia()` requires `localhost` or HTTPS.
- Without STUN/TURN, the project only targets localhost or simple same-LAN validation.
- `opencv-python-headless` does not provide GUI preview windows.
- This checklist is manual validation only. It is not a full E2E automation suite.