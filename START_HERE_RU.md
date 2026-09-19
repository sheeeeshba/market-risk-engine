# Запуск Multi-Asset Market Risk Engine

## Самый короткий путь

Откройте корневую папку проекта в VS Code. Встроенный Terminal должен показывать папку `market-risk-engine`.

Первая установка:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[dev]"
python -m streamlit run streamlit_app.py
```

Dashboard откроется по адресу `http://localhost:8501`. Оставьте Terminal открытым; для остановки нажмите `Control + C`.

При следующих запусках достаточно:

```bash
source .venv/bin/activate
python -m streamlit run streamlit_app.py
```

Также можно открыть Command Palette (`Shift + Command + P`) → `Tasks: Run Task` → `Risk Engine: dashboard`.

## Что смотреть в Demo

В sidebar оставьте `Data source` = `Demo snapshot`. Приложение сразу загрузит готовый воспроизводимый анализ без API-ключей.

- **Portfolio builder** — выберите preset, добавьте или удалите акции, ETF, облигации, металлы и сырьё, задайте веса и нажмите `Apply portfolio & recalculate all results`. Остаток до 100% автоматически станет USD cash.
- **Overview** — NAV, диапазоны VaR/ES и главный риск-драйвер.
- **Risk models** — сравнение Historical, Parametric Normal и Monte Carlo; можно переключить столбцы на confidence curve.
- **Backtesting** — rolling forecasts, исключения и тесты Купика/Кристофферсена.
- **Stress tests** — шесть гипотетических сценариев, искусственные crisis fixtures и distribution stress.
- **Risk contributions** — риск по позициям, классам активов и факторам.
- **Portfolio & P&L** — переключаемые NAV, Daily P&L и Cumulative P&L, а также последние позиции.
- **Evidence & downloads** — отчёт, one-page summary и полный ZIP evidence bundle.

В блоке **View controls** можно независимо настроить:

- confidence level: 95%, 97.5% или 99%;
- модели, которые видны на графиках;
- глубину истории: все даты, 12, 6 или 3 месяца;
- формат денег: USD, тысячи или миллионы;
- представление риска: USD loss или `% of NAV`;
- количество крупнейших risk drivers.

Эти настройки меняют только представление уже рассчитанных данных. Настройки в **Portfolio builder** меняют сам портфель: после `Apply` одновременно пересчитываются NAV/P&L, VaR/ES, backtesting, stress tests и risk contributions. Кнопка `Run risk analysis` повторно запускает текущий активный портфель.

### Как собрать свой портфель

1. Откройте вкладку **Portfolio builder** и выберите один из четырёх стартовых presets.
2. В поле **Included funded instruments** удалите ненужные позиции или добавьте новые из каталога 26 инструментов.
3. В таблице измените `Weight %`. Сумма инвестированной части не должна превышать 100%; остаток cash рассчитывается автоматически.
4. При необходимости настройте EUR/USD overlay. Он считается отдельно от funded weights.
5. Проверьте круговую диаграмму и нажмите **Apply portfolio & recalculate all results**.
6. Откройте остальные вкладки: все числа и графики уже относятся к новому портфелю. В **Evidence & downloads** можно скачать отдельный ZIP с его конфигурацией и таблицами.

Demo использует синтетические факторы. Его цифры подтверждают работу кода, но не являются исторической доходностью или результатом реального портфеля.

## Запуск из командной строки

```bash
# Полный pipeline
python -m market_risk run --config config/model_config.yaml --data-mode snapshot

# Тесты и lint
python -m pytest -q
python -m ruff check .

# Альтернативный запуск dashboard через CLI
market-risk app
```

Ожидаемый результат версии 1.1: `34 passed`, включая тесты конструктора портфеля, связанного пересчёта, dashboard, download layer и блокировку Live mode без ключа.

## Live data

Live mode требует дополнительные библиотеки и бесплатный FRED API key:

```bash
python -m pip install ".[live,dev]"
```

Выберите `Live market data`, вставьте ключ в password-поле и нажмите `Run risk analysis`. Ключ используется только в текущем процессе и не сохраняется в отчётах или downloads.

## Если `.venv/bin/python` не найден

Проверьте, что Terminal находится в корне проекта:

```bash
pwd
ls pyproject.toml streamlit_app.py
```

Если файлы найдены, создайте окружение командами из раздела «Первая установка». Путь к папке нельзя вводить как отдельную команду; для перехода используется `cd "/полный/путь/к/market-risk-engine"`.
