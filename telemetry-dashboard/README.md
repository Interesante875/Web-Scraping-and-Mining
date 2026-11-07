# Smart Device Telemetry Dashboard

Flask backend + plain JavaScript frontend for monitoring storage devices.

## Run locally
```bash
pip3 install flask
python3 app.py            # backend + frontend on http://localhost:5001
bash demo.sh             # (another terminal) mock devices sending data
```
Open http://localhost:5001. The frontend (`static/index.html`) is served by Flask, so there's no separate frontend server.

## Files
- `app.py`: routes, validation, status thresholds
- `store.py`: in-memory data layer (all data access goes through `MemoryStore`)
- `static/index.html`: dashboard UI (list view, detail view, self-test button, polling)
- `demo.sh`: curl script that plays the role of the devices

## API contract
All bodies are JSON. Errors return `{"error": "<message>"}` with 400 (bad input), 404 (unknown device) or 409 (duplicate).

| Method | URL | Body | Success |
|---|---|---|---|
| POST | `/api/devices` | `{"id":"ssd-001","model":"Samsung 980","location":"Rack A"}` | 201, device |
| GET | `/api/devices` | none | 200, list of devices with `latest` reading + `status` |
| GET | `/api/devices/<id>` | none | 200, device + last 10 `telemetry`, `selftests`, `diagnostics` |
| POST | `/api/devices/<id>/telemetry` | `{"temperature":45,"power_cycles":120,"bytes_written":50000}` | 201, reading + timestamp |
| POST | `/api/devices/<id>/selftest` | none | 201, `{"id":1,"status":"triggered","triggered_at":"..."}` |
| POST | `/api/devices/<id>/diagnostics` | `{"result":"pass","errors":0,"log":"SMART OK"}` | 201, result + timestamp |

Sample response, `GET /api/devices`:
```json
[{"id":"ssd-001","model":"Samsung 980","location":"Rack A",
  "registered_at":"2026-01-01T10:00:00+00:00",
  "latest":{"temperature":43,"power_cycles":103,"bytes_written":3000,"timestamp":"..."},
  "status":"healthy"}]
```

## Design decisions and assumptions
- **Status rules**: `error` if temperature >= 70C or the last diagnostic failed; `warning` if temperature >= 60C; `healthy` otherwise; `unknown` if there's no telemetry yet.
- **Self-test flow**: the user clicks "Run self-test", which records a `triggered` self-test. When the device later POSTs diagnostics, the latest pending self-test is marked `completed`. In a real system the device would pick up the command by polling or through a message queue.
- **Persistence**: in-memory dicts inside `MemoryStore`. To move to a database, write e.g. a `SqlStore` with the same methods and change one line in `app.py`. Data resets when the server restarts.
- **Live updates**: the frontend polls every 3 seconds (no websockets).
- **No auth.** It's out of scope for this exercise.

## Demo workflow
1. Start `python3 app.py` and open http://localhost:5001.
2. Register a device in the form, or run `bash demo.sh`.
3. Send telemetry with curl (see `demo.sh`). The list updates within 3 seconds.
4. Click a row to open the detail view, then click **Run self-test**. A `triggered` entry appears.
5. POST a diagnostic result for that device. The self-test becomes `completed` and the result shows up in the table (a `fail` result turns the status red).
