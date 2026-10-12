"""Check fixture structure and references, not model safety or correctness."""

from collections import Counter
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.docs = json.loads((ROOT / "document-index.json").read_text(encoding="utf-8"))
        self.cases = json.loads((ROOT / "evaluation-cases.json").read_text(encoding="utf-8"))

    def test_case_ids_and_group_counts(self):
        self.assertEqual([c["id"] for c in self.cases], [f"Q{i:03d}" for i in range(1, 25)])
        self.assertEqual(Counter(c["category"] for c in self.cases),
                         dict(normal=8, insufficient=6, permissions=6, malicious=4))

    def test_documents_and_declared_versions_exist(self):
        self.assertEqual(len({d["id"] for d in self.docs}), 5)
        for doc in self.docs:
            path = ROOT / doc["path"]
            self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
            body = path.read_text(encoding="utf-8")
            for token in (doc["id"], doc["version"], doc["status"], doc["disclosure"]):
                self.assertIn(token, body)

    def test_public_current_evidence_only_and_not_executed(self):
        lookup = {d["id"]: d for d in self.docs}
        for case in self.cases:
            self.assertIn(case["expected_action"], {"answer", "clarify", "escalate", "refuse"})
            self.assertEqual(case["execution_status"], "not-run")
            self.assertTrue(case["required_constraint"])
            if case["expected_action"] == "answer":
                self.assertTrue(case["allowed_evidence"])
            for evidence in case["allowed_evidence"]:
                self.assertIn(evidence, lookup)
                self.assertEqual(lookup[evidence]["status"], "approved")
                self.assertEqual(lookup[evidence]["disclosure"], "public")


if __name__ == "__main__":
    unittest.main()
