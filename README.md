# Croatian Holidays

[![PyPI version](https://img.shields.io/pypi/v/croatian-holidays.svg)](https://pypi.org/project/croatian-holidays/)
[![Python versions](https://img.shields.io/pypi/pyversions/croatian-holidays.svg)](https://pypi.org/project/croatian-holidays/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A lightweight Python utility for **Croatian public holidays**: compute holidays for any year, check if today is a holiday, list upcoming holidays, and optionally scrape an external reference page.

- **Pure Python** for computed holidays (Easter, Corpus Christi, + fixed dates)
- **Typed exceptions** and **no print spam** (uses `logging`)
- **Optional web parsing** with timeouts and structural checks
- Pretty-print and JSON save helpers

> Project name on PyPI is **`croatian-holidays`**, while the import name is **`croatian_holidays`**.
> You can check it out on https://pypi.org/project/croatian-holidays/0.1.0/

## Installation

```bash
pip install croatian-holidays
```

or

```bash
pip install croatian-holidays==0.1.0 ## For specific versions
```


## Quick start

```python
import datetime as dt
from croatian_holidays import CroatianHolidays

ch = CroatianHolidays()

# 1) Is today a holiday?
print("Today is holiday:", ch.isHoliday())

# 2) All holidays for a year
hol_2025 = ch.getHolidays(2025)  # dict: "dd. mm. yyyy." -> "Holiday name"
print(hol_2025["01. 05. 2025."])  # "Praznik rada"

# 3) Include localized day-of-week and pretty output
print(ch.getHolidays(2025, showdays=True, prettyprint=True))

# 4) Upcoming holidays after now (current year)
print(ch.upcomingHolidays(date=dt.datetime.now(), showdays=True, prettyPrint=True))

# 5) Holidays between two dates (inclusive)
print(ch.getHolidaysBetweenDates("01. 05. 2025.", "31. 12. 2025.", showdays=True, prettyPrint=True))

# 6) Persist to JSON
data = ch.getHolidays(2025, showdays=True)
from croatian_holidays import SaveError
try:
    ch.saveToJson(data, "croatia_2025_holidays.json")
except SaveError as e:
    print("Saving failed:", e)
```

## Features

- ✅ **Algorithmic dates**: Easter (Meeus/Jones/Butcher), Corpus Christi (+60 days)
- ✅ **Fixed-date holidays**: New Year’s, Statehood Day, All Saints’, etc.
- ✅ **Features**:
  - `getHolidays(year, showdays=False, prettyprint=False)`
  - `upcomingHolidays(date, showdays=False, prettyPrint=False)`
  - `getHolidaysBetweenDates(start_date, end_date, showdays=False, prettyPrint=False)`
  - `isHoliday()`
  - `getHolidaysFromWeb(base_url=..., prettyPrint=False, timeout=10.0, ...)`
  - `prettyPrint(dict)`
  - `saveToJson(dict, filename)`
- 🧯 **Errors are explicit** and do not leak prints, using logger
- 🧰 **Logging-friendly**: ships with a `NullHandler`; opt-in to logs in your app.

## Module Reference

> Date strings use `"dd. mm. yyyy."` (note the trailing dot).  

### `CroatianHolidays.getHolidays(year, showdays=False, prettyprint=False) -> dict | str`
Return holidays for `year`.  
- `showdays=True` → values become `{ "name": ..., "day_of_week": ... }` (Croatian weekday).
- `prettyprint=True` → returns pretty JSON `str` instead of `dict`.

### `CroatianHolidays.upcomingHolidays(date, showdays=False, prettyPrint=False) -> dict | str`
Return upcoming holidays **after** the given `datetime` (current year only).

### `CroatianHolidays.getHolidaysBetweenDates(start_date, end_date, showdays=False, prettyPrint=False, dateformat="%d. %m. %Y.") -> dict | str`
Return holidays within an **inclusive** range. `start_date`/`end_date` can be `str`, `date`, or `datetime`.

### `CroatianHolidays.isHoliday() -> bool`
True if **today** is a holiday.

### `CroatianHolidays.getHolidaysFromWeb(base_url=..., prettyPrint=False, timeout=10.0, session=None, user_agent=None) -> dict | str`
Try to parse an external web page for holidays

### `CroatianHolidays.prettyPrint(json_data: dict) -> str`
Pretty JSON with UTF-8 (no ASCII escapes).

### `CroatianHolidays.saveToJson(data: dict, filename: str, encoding="utf-8") -> None`
Write a dictionary to a JSON file.

## Exceptions

Import from the package root:

```python
from croatian_holidays import (
    CroatianHolidaysError, InvalidYearError, DateFormatError,
    NetworkError, ParseError, SaveError
)
```

- `InvalidYearError`: year must be `1583..4099` (Gregorian computus range).
- `DateFormatError`: invalid date strings / formatting issues.
- `NetworkError`: timeouts, connection issues, HTTP errors in web fetch.
- `ParseError`: the web page did not match expected structure.
- `SaveError`: file write errors.
- `CroatianHolidaysError`: base class for all package errors.

## Logging

By default, the library is quiet. To see warnings or debug messages:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Development

```bash
git clone https://github.com/mgracanin/croatian-holidays.git
cd croatian-holidays
python -m venv .venv && source .venv/bin/activate  # or use whatever you like
pip install -e .
```

Recommended tooling (optional):
- **ruff** for linting
- **mypy** for typing
- **pytest** for tests

## Versioning & Compatibility

- Python **3.8+**
- Semantic-ish versioning; breaking API changes bump the minor/major.

## License

MIT — see [LICENSE](LICENSE).
