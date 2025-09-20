"""A/B testing for email subject lines and templates."""

import random
import json
import os
from datetime import datetime


class ABTest:
    def __init__(self, test_name: str, variants: list[str]):
        self.test_name = test_name
        self.variants = variants
        self.results_file = f".ab_results_{test_name}.json"
        self.results = self._load_results()

    def _load_results(self) -> dict:
        if os.path.exists(self.results_file):
            with open(self.results_file) as f:
                return json.load(f)
        return {v: {"sent": 0, "opened": 0, "replied": 0} for v in self.variants}

    def _save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results, f, indent=2)

    def get_variant(self) -> str:
        # Pick variant with least sends for even distribution
        min_sends = min(self.results[v]["sent"] for v in self.variants)
        candidates = [v for v in self.variants if self.results[v]["sent"] == min_sends]
        return random.choice(candidates)

    def record_send(self, variant: str):
        self.results[variant]["sent"] += 1
        self._save_results()

    def record_open(self, variant: str):
        self.results[variant]["opened"] += 1
        self._save_results()

    def record_reply(self, variant: str):
        self.results[variant]["replied"] += 1
        self._save_results()

    def get_stats(self) -> dict:
        stats = {}
        for v in self.variants:
            r = self.results[v]
            sent = r["sent"] or 1
            stats[v] = {
                "sent": r["sent"],
                "open_rate": f"{r['opened']/sent*100:.1f}%",
                "reply_rate": f"{r['replied']/sent*100:.1f}%",
            }
        return stats
