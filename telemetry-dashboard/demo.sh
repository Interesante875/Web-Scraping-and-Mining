#!/bin/bash
# Demo: simulates devices talking to the backend. Run while app.py is running.
URL=http://localhost:5001/api
H="Content-Type: application/json"

curl -s -X POST $URL/devices -H "$H" -d '{"id":"ssd-001","model":"Samsung 980","location":"Rack A"}'; echo
curl -s -X POST $URL/devices -H "$H" -d '{"id":"ssd-002","model":"Crucial P5","location":"Rack B"}'; echo

for i in 1 2 3; do
  curl -s -X POST $URL/devices/ssd-001/telemetry -H "$H" \
    -d "{\"temperature\":$((40 + i)),\"power_cycles\":$((100 + i)),\"bytes_written\":$((1000 * i))}"; echo
done
curl -s -X POST $URL/devices/ssd-002/telemetry -H "$H" \
  -d '{"temperature":72,"power_cycles":50,"bytes_written":5000}'; echo

curl -s -X POST $URL/devices/ssd-001/selftest; echo
curl -s -X POST $URL/devices/ssd-001/diagnostics -H "$H" \
  -d '{"result":"pass","errors":0,"log":"SMART OK"}'; echo
