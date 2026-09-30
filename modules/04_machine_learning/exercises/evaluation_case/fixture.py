"""Synthetic support snapshot, generated only by explicit calls."""

import json
import random


def dataset_bytes() -> bytes:
    randomizer = random.Random(41)
    rows = []
    for index in range(96):
        label = randomizer.randrange(2)
        rows.append(
            {
                "id": f"ticket-{index:03}",
                "account_id": f"account-{index // 3:02}",
                "opened_day": index // 4,
                "channel": randomizer.randrange(3),
                "message_length": randomizer.randrange(15, 350),
                "service_code": 20 + 50 * label + randomizer.randrange(5),
                "touches": randomizer.randrange(1, 7),
                "label": label,
            }
        )
    return (json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n").encode()


def candidate_split() -> dict[str, list[str]]:
    row_ids = [row["id"] for row in json.loads(dataset_bytes())]
    random.Random(7).shuffle(row_ids)
    return {"train_ids": row_ids[:64], "test_ids": row_ids[64:]}
