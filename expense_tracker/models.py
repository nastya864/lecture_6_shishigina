from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


INCOME = "income"
EXPENSE = "expense"
VALID_TYPES = {INCOME, EXPENSE}

INCOME_CATEGORIES = (
    "Зарплата",
    "Подработка",
    "Продажи",
    "Инвестиции",
    "Подарки",
    "Прочее",
)

EXPENSE_CATEGORIES = (
    "Офис",
    "Зарплаты",
    "Маркетинг",
    "Логистика",
    "Налоги",
    "Прочее",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True, slots=True)
class Transaction:
    id: str
    type: str
    category: str
    description: str
    amount: float
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if self.type not in VALID_TYPES:
            raise ValueError("Тип операции должен быть income или expense")
        if not self.category.strip():
            raise ValueError("Категория не может быть пустой")
        if not self.description.strip():
            raise ValueError("Описание не может быть пустым")
        if self.amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")

    @classmethod
    def create(
        cls,
        transaction_type: str,
        category: str,
        description: str,
        amount: float,
    ) -> "Transaction":
        timestamp = utc_now()
        return cls(
            id=uuid.uuid4().hex,
            type=transaction_type,
            category=category.strip(),
            description=description.strip(),
            amount=round(float(amount), 2),
            created_at=timestamp,
            updated_at=timestamp,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        created_at = str(data.get("created_at") or utc_now())
        return cls(
            id=str(data.get("id") or uuid.uuid4().hex),
            type=str(data["type"]),
            category=str(data["category"]),
            description=str(data["description"]),
            amount=round(float(data["amount"]), 2),
            created_at=created_at,
            updated_at=str(data.get("updated_at") or created_at),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class TransactionStore:
    """JSON-backed store used by both the UI and cloud synchronization."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.transactions: list[Transaction] = []

    def load(self) -> list[Transaction]:
        if not self.path.exists():
            self.transactions = []
            return self.transactions

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Не удалось прочитать локальные данные: {exc}") from exc

        if not isinstance(raw, list):
            raise ValueError("Локальный файл должен содержать список операций")
        self.transactions = [Transaction.from_dict(item) for item in raw]
        self.transactions.sort(key=lambda item: item.created_at, reverse=True)
        return self.transactions

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in self.transactions]
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def add(
        self,
        transaction_type: str,
        category: str,
        description: str,
        amount: float,
    ) -> Transaction:
        transaction = Transaction.create(
            transaction_type, category, description, amount
        )
        self.transactions.insert(0, transaction)
        self.save()
        return transaction

    def delete(self, transaction_id: str) -> bool:
        original_count = len(self.transactions)
        self.transactions = [
            item for item in self.transactions if item.id != transaction_id
        ]
        changed = len(self.transactions) != original_count
        if changed:
            self.save()
        return changed

    def replace_all(self, transactions: Iterable[Transaction]) -> None:
        self.transactions = sorted(
            list(transactions), key=lambda item: item.created_at, reverse=True
        )
        self.save()

    @property
    def total_income(self) -> float:
        return round(
            sum(item.amount for item in self.transactions if item.type == INCOME), 2
        )

    @property
    def total_expense(self) -> float:
        return round(
            sum(item.amount for item in self.transactions if item.type == EXPENSE), 2
        )

    @property
    def balance(self) -> float:
        return round(self.total_income - self.total_expense, 2)

    def totals_by_category(self, transaction_type: str) -> dict[str, float]:
        if transaction_type not in VALID_TYPES:
            raise ValueError("Неизвестный тип операции")
        result: dict[str, float] = {}
        for item in self.transactions:
            if item.type == transaction_type:
                result[item.category] = round(
                    result.get(item.category, 0.0) + item.amount, 2
                )
        return dict(sorted(result.items(), key=lambda pair: pair[1], reverse=True))
