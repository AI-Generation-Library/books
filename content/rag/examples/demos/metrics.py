import json
from ragbook.metrics import retrieval_metrics

if __name__ == "__main__":
    print(
        json.dumps(
            retrieval_metrics(["X", "A", "A", "B"], {"A": 2, "B": 1}, 3), indent=2
        )
    )
