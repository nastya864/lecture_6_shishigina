import json
import tempfile
import unittest
from pathlib import Path

from expense_tracker.models import EXPENSE, INCOME, Transaction, TransactionStore


class TransactionStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "transactions.json"
        self.store = TransactionStore(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_add_save_and_load(self):
        created = self.store.add(INCOME, "Продажи", "Заказ", 1250.50)
        loaded = TransactionStore(self.path)
        loaded.load()
        self.assertEqual(loaded.transactions[0].id, created.id)
        self.assertEqual(loaded.total_income, 1250.50)

    def test_balance_and_category_totals(self):
        self.store.add(INCOME, "Продажи", "Заказ 1", 1000)
        self.store.add(INCOME, "Продажи", "Заказ 2", 500)
        self.store.add(EXPENSE, "Маркетинг", "Реклама", 400)
        self.assertEqual(self.store.total_income, 1500)
        self.assertEqual(self.store.total_expense, 400)
        self.assertEqual(self.store.balance, 1100)
        self.assertEqual(self.store.totals_by_category(INCOME), {"Продажи": 1500})

    def test_invalid_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add(EXPENSE, "Офис", "Бумага", 0)

    def test_unknown_transaction_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add("transfer", "Офис", "Перевод", 100)

    def test_empty_category_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add(EXPENSE, "  ", "Бумага", 100)

    def test_empty_description_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add(EXPENSE, "Офис", "  ", 100)

    def test_delete(self):
        created = self.store.add(EXPENSE, "Офис", "Бумага", 100)
        self.assertTrue(self.store.delete(created.id))
        self.assertFalse(self.store.delete(created.id))
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), [])

    def test_legacy_record_gets_sync_fields(self):
        transaction = Transaction.from_dict(
            {
                "type": EXPENSE,
                "category": "Офис",
                "description": "Ручки",
                "amount": 50,
            }
        )
        self.assertTrue(transaction.id)
        self.assertEqual(transaction.created_at, transaction.updated_at)

    def test_missing_file_loads_as_empty_store(self):
        self.assertEqual(self.store.load(), [])

    def test_invalid_json_is_rejected(self):
        self.path.write_text("not-json", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.load()

    def test_replace_all_persists_merged_data(self):
        first = Transaction.create(INCOME, "Продажи", "Заказ", 100)
        second = Transaction.create(EXPENSE, "Офис", "Бумага", 25)
        self.store.replace_all([first, second])
        loaded = TransactionStore(self.path)
        loaded.load()
        self.assertEqual({item.id for item in loaded.transactions}, {first.id, second.id})


if __name__ == "__main__":
    unittest.main()
