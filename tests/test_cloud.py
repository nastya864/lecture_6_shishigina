import unittest

from expense_tracker.cloud import merge_transactions
from expense_tracker.models import INCOME, Transaction


def transaction(identifier: str, amount: float, updated_at: str) -> Transaction:
    return Transaction(
        id=identifier,
        type=INCOME,
        category="Продажи",
        description="Заказ",
        amount=amount,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at=updated_at,
    )


class MergeTests(unittest.TestCase):
    def test_empty_sources_produce_empty_result(self):
        self.assertEqual(merge_transactions([], []), [])

    def test_merge_keeps_unique_records(self):
        merged = merge_transactions(
            [transaction("local", 100, "2026-01-01T00:00:00+00:00")],
            [transaction("remote", 200, "2026-01-01T00:00:00+00:00")],
        )
        self.assertEqual({item.id for item in merged}, {"local", "remote"})

    def test_latest_record_wins_conflict(self):
        merged = merge_transactions(
            [transaction("same", 100, "2026-01-01T00:00:00+00:00")],
            [transaction("same", 250, "2026-01-02T00:00:00+00:00")],
        )
        self.assertEqual(merged[0].amount, 250)

    def test_local_record_wins_when_it_is_newer(self):
        merged = merge_transactions(
            [transaction("same", 300, "2026-01-03T00:00:00+00:00")],
            [transaction("same", 250, "2026-01-02T00:00:00+00:00")],
        )
        self.assertEqual(merged[0].amount, 300)


if __name__ == "__main__":
    unittest.main()
