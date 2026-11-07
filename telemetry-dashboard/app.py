"""Smart Device Telemetry Dashboard - Flask backend.

Run:  python3 app.py   then open http://localhost:5001
"""
from flask import Flask, jsonify, request, send_from_directory

from store import MemoryStore

app = Flask(__name__, static_folder="static")
db = MemoryStore()

# Status thresholds (temperature in Celsius)
TEMP_WARNING = 60
TEMP_ERROR = 70


def error(message, code):
    return jsonify({"error": message}), code


def compute_status(device_id):
    """healthy / warning / error based on latest telemetry + diagnostics."""
    readings = db.get_telemetry(device_id, limit=1)
    if not readings:
        return "unknown"
    diags = db.get_diagnostics(device_id)
    if diags and diags[-1]["result"] == "fail":
        return "error"
    temp = readings[-1]["temperature"]
    if temp >= TEMP_ERROR:
        return "error"
    if temp >= TEMP_WARNING:
        return "warning"
    return "healthy"


def device_summary(device):
    readings = db.get_telemetry(device["id"], limit=1)
    return {**device,
            "latest": readings[-1] if readings else None,
            "status": compute_status(device["id"])}


def require_device(device_id):
    device = db.get_device(device_id)
    if device is None:
        return None, error(f"Device '{device_id}' not found", 404)
    return device, None


# ---------------- Frontend ----------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ---------------- Devices ----------------
@app.route("/api/devices", methods=["POST"])
def register_device():
    data = request.get_json(silent=True)
    if not data or not data.get("id"):
        return error("'id' is required", 400)
    if db.get_device(data["id"]):
        return error(f"Device '{data['id']}' already exists", 409)
    device = db.add_device(data["id"], data.get("model", ""), data.get("location", ""))
    return jsonify(device), 201


@app.route("/api/devices", methods=["GET"])
def list_devices():
    return jsonify([device_summary(d) for d in db.list_devices()])


@app.route("/api/devices/<device_id>", methods=["GET"])
def get_device(device_id):
    device, err = require_device(device_id)
    if err:
        return err
    return jsonify({**device_summary(device),
                    "telemetry": db.get_telemetry(device_id, limit=10),
                    "selftests": db.get_selftests(device_id),
                    "diagnostics": db.get_diagnostics(device_id)})


# ---------------- Telemetry ----------------
@app.route("/api/devices/<device_id>/telemetry", methods=["POST"])
def post_telemetry(device_id):
    _, err = require_device(device_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    fields = ["temperature", "power_cycles", "bytes_written"]
    for f in fields:
        if not isinstance(data.get(f), (int, float)) or isinstance(data.get(f), bool):
            return error(f"'{f}' is required and must be a number", 400)
    reading = db.add_telemetry(device_id, {f: data[f] for f in fields})
    return jsonify(reading), 201


# ---------------- Self-test ----------------
@app.route("/api/devices/<device_id>/selftest", methods=["POST"])
def trigger_selftest(device_id):
    _, err = require_device(device_id)
    if err:
        return err
    return jsonify(db.add_selftest(device_id)), 201


# ---------------- Diagnostics ----------------
@app.route("/api/devices/<device_id>/diagnostics", methods=["POST"])
def post_diagnostics(device_id):
    _, err = require_device(device_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    if data.get("result") not in ("pass", "fail"):
        return error("'result' must be 'pass' or 'fail'", 400)
    errors = data.get("errors", 0)
    if not isinstance(errors, int):
        return error("'errors' must be an integer", 400)
    result = db.add_diagnostic(device_id, {"result": data["result"], "errors": errors,
                                           "log": str(data.get("log", ""))[:500]})
    return jsonify(result), 201


if __name__ == "__main__":
    app.run(debug=True, port=5001)
