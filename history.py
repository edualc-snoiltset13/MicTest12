import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "calc_history.json"


class CalculationHistory:
    def __init__(self):
        self._entries = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            self._entries = json.loads(HISTORY_FILE.read_text())

    def _save(self):
        HISTORY_FILE.write_text(json.dumps(self._entries, indent=2))

    def record(self, a, operator, b, result):
        entry = {
            "expression": f"{a} {operator} {b}",
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        self._entries.append(entry)
        self._save()

    def get_all(self):
        return list(self._entries)

    def get_last(self, n=1):
        return self._entries[-n:]

    def search(self, query):
        return [e for e in self._entries if query in e["expression"]]

    def clear(self):
        self._entries = []
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()

    def __len__(self):
        return len(self._entries)
