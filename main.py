from __future__ import annotations

import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from expense_tracker.charts import build_summary_figure
from expense_tracker.cloud import FirebaseClient
from expense_tracker.models import (
    EXPENSE,
    EXPENSE_CATEGORIES,
    INCOME,
    INCOME_CATEGORIES,
    TransactionStore,
)

try:
    from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
except ImportError:  # Compatibility with the import used in the lecture.
    try:
        from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
    except ImportError:
        FigureCanvasKivyAgg = None


Window.minimum_width = 780
Window.minimum_height = 600


class ExpenseTrackerRoot(BoxLayout):
    def __init__(self, store: TransactionStore, **kwargs):
        super().__init__(orientation="vertical", padding=dp(16), spacing=dp(10), **kwargs)
        self.store = store
        self.summary = Label(size_hint_y=None, height=dp(72), markup=True)
        self.add_widget(self.summary)

        actions = GridLayout(cols=5, size_hint_y=None, height=dp(48), spacing=dp(8))
        actions.add_widget(self._button("Добавить", self.open_add_popup, (0.15, 0.55, 0.35, 1)))
        actions.add_widget(self._button("Графики", self.open_charts, (0.2, 0.35, 0.7, 1)))
        actions.add_widget(self._button("Облако", self.sync_cloud, (0.2, 0.55, 0.75, 1)))
        actions.add_widget(self._button("CSV", self.export_csv, (0.85, 0.5, 0.15, 1)))
        actions.add_widget(self._button("Обновить", self.refresh, (0.4, 0.4, 0.4, 1)))
        self.add_widget(actions)

        self.rows = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.rows.bind(minimum_height=self.rows.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.rows)
        self.add_widget(scroll)
        self.refresh()

    @staticmethod
    def _button(text, callback, color):
        button = Button(text=text, background_color=color)
        button.bind(on_release=callback)
        return button

    def refresh(self, *_):
        self.summary.text = (
            "[b]БИЗНЕС-ТРЕКЕР[/b]\n"
            f"[color=2a9d8f]Доходы: {self.store.total_income:,.2f} руб.[/color]    "
            f"[color=e76f51]Расходы: {self.store.total_expense:,.2f} руб.[/color]    "
            f"[b]Баланс: {self.store.balance:,.2f} руб.[/b]"
        )
        self.rows.clear_widgets()
        if not self.store.transactions:
            self.rows.add_widget(
                Label(
                    text="Операций пока нет. Нажмите «Добавить».",
                    size_hint_y=None,
                    height=dp(60),
                )
            )
            return

        for transaction in self.store.transactions:
            row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
            sign = "+" if transaction.type == INCOME else "−"
            color = "2a9d8f" if transaction.type == INCOME else "e76f51"
            label = Label(
                text=(
                    f"[b]{transaction.category}[/b]  {transaction.description}\n"
                    f"[color={color}]{sign}{transaction.amount:,.2f} руб.[/color]"
                ),
                markup=True,
                halign="left",
                valign="middle",
            )
            label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
            delete = Button(text="Удалить", size_hint_x=None, width=dp(90))
            delete.bind(
                on_release=lambda _, item_id=transaction.id: self.delete_transaction(item_id)
            )
            row.add_widget(label)
            row.add_widget(delete)
            self.rows.add_widget(row)

    def open_add_popup(self, *_):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        transaction_type = Spinner(text="Расход", values=("Расход", "Доход"))
        category = Spinner(text=EXPENSE_CATEGORIES[0], values=EXPENSE_CATEGORIES)
        description = TextInput(hint_text="Описание", multiline=False)
        amount = TextInput(hint_text="Сумма", multiline=False, input_filter="float")

        def update_categories(*_args):
            values = INCOME_CATEGORIES if transaction_type.text == "Доход" else EXPENSE_CATEGORIES
            category.values = values
            category.text = values[0]

        transaction_type.bind(text=update_categories)
        for widget in (transaction_type, category, description, amount):
            content.add_widget(widget)

        buttons = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        cancel = Button(text="Отмена")
        save = Button(text="Сохранить", background_color=(0.15, 0.55, 0.35, 1))
        buttons.add_widget(cancel)
        buttons.add_widget(save)
        content.add_widget(buttons)
        popup = Popup(title="Новая операция", content=content, size_hint=(0.72, 0.72))
        cancel.bind(on_release=popup.dismiss)

        def save_transaction(*_args):
            try:
                self.store.add(
                    INCOME if transaction_type.text == "Доход" else EXPENSE,
                    category.text,
                    description.text,
                    float(amount.text.replace(",", ".")),
                )
            except (ValueError, TypeError) as exc:
                self.show_message("Ошибка", str(exc) or "Проверьте введённые данные")
                return
            popup.dismiss()
            self.refresh()

        save.bind(on_release=save_transaction)
        popup.open()

    def delete_transaction(self, transaction_id: str):
        self.store.delete(transaction_id)
        self.refresh()

    def open_charts(self, *_):
        if FigureCanvasKivyAgg is None:
            self.show_message(
                "Не установлен модуль графиков",
                "В терминале PyCharm выполните: garden install matplotlib",
            )
            return
        figure = build_summary_figure(self.store)
        content = BoxLayout(orientation="vertical")
        content.add_widget(FigureCanvasKivyAgg(figure))
        close = Button(text="Закрыть", size_hint_y=None, height=dp(44))
        content.add_widget(close)
        popup = Popup(title="Аналитика", content=content, size_hint=(0.94, 0.9))
        close.bind(on_release=popup.dismiss)
        popup.open()

    def sync_cloud(self, *_):
        database_url = os.getenv("FIREBASE_DATABASE_URL", "").strip()
        if not database_url:
            self.show_message(
                "Firebase не настроен",
                "Скопируйте .env.example в .env и укажите FIREBASE_DATABASE_URL.",
            )
            return
        self.show_message("Синхронизация", "Обмен данными с Firebase начат…")
        Clock.schedule_once(lambda _dt: self._perform_sync(database_url), 0.1)

    def _perform_sync(self, database_url: str):
        try:
            client = FirebaseClient(
                database_url=database_url,
                auth_token=os.getenv("FIREBASE_AUTH_TOKEN", ""),
            )
            merged = client.synchronize(self.store.transactions)
            self.store.replace_all(merged)
        except Exception as exc:
            self.show_message("Ошибка синхронизации", str(exc))
            return
        self.refresh()
        self.show_message("Готово", "Локальные и облачные данные синхронизированы.")

    def export_csv(self, *_):
        output = Path(App.get_running_app().user_data_dir) / "transactions_export.csv"
        with output.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(["Тип", "Категория", "Описание", "Сумма", "Дата"])
            for item in self.store.transactions:
                writer.writerow(
                    [item.type, item.category, item.description, item.amount, item.created_at]
                )
        self.show_message("Экспорт завершён", f"Файл сохранён:\n{output}")

    @staticmethod
    def show_message(title: str, message: str):
        content = Label(text=message, halign="center", valign="middle")
        content.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        Popup(title=title, content=content, size_hint=(0.72, 0.42)).open()


class ExpenseTrackerApp(App):
    title = "Business Expense Tracker"

    def build(self):
        load_dotenv()
        data_path = Path(self.user_data_dir) / "transactions.json"
        store = TransactionStore(data_path)
        try:
            store.load()
        except ValueError:
            store.transactions = []
        return ExpenseTrackerRoot(store)


if __name__ == "__main__":
    ExpenseTrackerApp().run()
