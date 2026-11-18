# Kivy Expense Tracker

Учебное мобильное приложение к лекции 6 по дисциплине «Проектирование и разработка бизнес-ориентированного программного обеспечения».

Приложение позволяет:

- добавлять доходы и расходы по категориям;
- автоматически рассчитывать доходы, расходы и баланс;
- строить графики по категориям;
- хранить операции локально в JSON;
- синхронизировать данные с Firebase Realtime Database через REST API;
- экспортировать операции в CSV.

## Запуск в PyCharm

1. Откройте в PyCharm папку `kivy-expense-tracker`.
2. Выберите Python 3.11 или 3.12 и создайте виртуальное окружение `.venv`.
3. Откройте встроенный терминал PyCharm и установите зависимости:

```bash
python -m pip install -r requirements.txt
garden install matplotlib
```

4. Запустите файл `main.py` кнопкой Run.

## Настройка Firebase

1. Создайте проект и Realtime Database в Firebase.
2. Скопируйте `.env.example` в `.env`.
3. Вставьте URL базы данных:

```dotenv
FIREBASE_DATABASE_URL=https://example-default-rtdb.firebaseio.com
```

Если правила базы требуют авторизацию, добавьте токен в `FIREBASE_AUTH_TOKEN`. Файл `.env` исключён из Git и не должен публиковаться.

Кнопка «Облако» загружает данные из Firebase, объединяет их с локальными операциями по идентификатору и времени изменения, после чего сохраняет объединённый набор локально и в облаке.

## Тесты

Тесты бизнес-логики не требуют запуска графического интерфейса:

```bash
python -m unittest discover -s tests -v
```

## Структура проекта

```text
kivy-expense-tracker/
├── expense_tracker/
│   ├── models.py       # операции, категории, баланс и локальное хранение
│   ├── charts.py       # графики доходов и расходов
│   └── cloud.py        # синхронизация Firebase REST API
├── tests/              # автоматические тесты
├── main.py             # интерфейс Kivy
├── requirements.txt
├── .env.example
└── .gitignore
```
