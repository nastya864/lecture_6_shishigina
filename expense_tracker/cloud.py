from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Transaction


def merge_transactions(
    local: Iterable[Transaction], remote: Iterable[Transaction]
) -> list[Transaction]:
    """Merge records by id; the record with the latest updated_at wins."""
    merged: dict[str, Transaction] = {}
    for item in [*local, *remote]:
        current = merged.get(item.id)
        if current is None or item.updated_at >= current.updated_at:
            merged[item.id] = item
    return sorted(merged.values(), key=lambda item: item.created_at, reverse=True)


@dataclass(slots=True)
class FirebaseClient:
    database_url: str
    auth_token: str = ""
    collection: str = "transactions"
    timeout: int = 15

    def __post_init__(self) -> None:
        self.database_url = self.database_url.strip().rstrip("/")
        if not self.database_url.startswith(("https://", "http://")):
            raise ValueError("Некорректный FIREBASE_DATABASE_URL")

    @property
    def endpoint(self) -> str:
        return f"{self.database_url}/{self.collection}.json"

    def _params(self) -> dict[str, str]:
        return {"auth": self.auth_token} if self.auth_token else {}

    def download(self) -> list[Transaction]:
        import requests

        response = requests.get(
            self.endpoint, params=self._params(), timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json()
        if payload is None:
            return []
        if isinstance(payload, dict):
            records = payload.values()
        elif isinstance(payload, list):
            records = payload
        else:
            raise ValueError("Firebase вернул данные неизвестного формата")
        return [Transaction.from_dict(item) for item in records if item]

    def upload(self, transactions: Iterable[Transaction]) -> None:
        import requests

        payload = {item.id: item.to_dict() for item in transactions}
        response = requests.put(
            self.endpoint,
            params=self._params(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

    def synchronize(self, local: Iterable[Transaction]) -> list[Transaction]:
        merged = merge_transactions(local, self.download())
        self.upload(merged)
        return merged
