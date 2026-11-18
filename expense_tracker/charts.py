from __future__ import annotations

from matplotlib.figure import Figure

from .models import EXPENSE, INCOME, TransactionStore


def build_summary_figure(store: TransactionStore) -> Figure:
    """Build two category charts without depending on Kivy."""
    figure = Figure(figsize=(8, 5), constrained_layout=True)
    expense_axis, income_axis = figure.subplots(1, 2)

    _draw_category_chart(
        expense_axis,
        store.totals_by_category(EXPENSE),
        "Расходы по категориям",
        "#e76f51",
    )
    _draw_category_chart(
        income_axis,
        store.totals_by_category(INCOME),
        "Доходы по категориям",
        "#2a9d8f",
    )
    return figure


def _draw_category_chart(axis, values: dict[str, float], title: str, color: str) -> None:
    axis.set_title(title)
    if not values:
        axis.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        axis.set_axis_off()
        return
    labels = list(values)
    amounts = list(values.values())
    axis.barh(labels, amounts, color=color)
    axis.invert_yaxis()
    axis.set_xlabel("Сумма, руб.")
    axis.grid(axis="x", alpha=0.2)
