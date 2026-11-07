"""In-memory data store.

All data access goes through this class, so swapping to SQL/NoSQL later
only means writing another class with the same methods.
"""
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    def __init__(self):
        self.devices = {}      # device_id -> {id, model, location, registered_at}
        self.telemetry = {}    # device_id -> [readings]
        self.selftests = {}    # device_id -> [self-test records]
        self.diagnostics = {}  # device_id -> [diagnostic results]

    # ---- devices ----
    def add_device(self, device_id, model, location):
        device = {"id": device_id, "model": model, "location": location,
                  "registered_at": now()}
        self.devices[device_id] = device
        self.telemetry[device_id] = []
        self.selftests[device_id] = []
        self.diagnostics[device_id] = []
        return device

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def list_devices(self):
        return list(self.devices.values())

    # ---- telemetry ----
    def add_telemetry(self, device_id, reading):
        reading["timestamp"] = now()
        self.telemetry[device_id].append(reading)
        return reading

    def get_telemetry(self, device_id, limit=10):
        return self.telemetry[device_id][-limit:]

    # ---- self-tests ----
    def add_selftest(self, device_id):
        test = {"id": len(self.selftests[device_id]) + 1,
                "status": "triggered", "triggered_at": now()}
        self.selftests[device_id].append(test)
        return test

    def get_selftests(self, device_id):
        return self.selftests[device_id]

    # ---- diagnostics ----
    def add_diagnostic(self, device_id, result):
        result["timestamp"] = now()
        self.diagnostics[device_id].append(result)
        # Mark the latest pending self-test as completed
        for test in reversed(self.selftests[device_id]):
            if test["status"] == "triggered":
                test["status"] = "completed"
                break
        return result

    def get_diagnostics(self, device_id):
        return self.diagnostics[device_id]
