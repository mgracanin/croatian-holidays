from __future__ import annotations

import datetime
import json
import logging
from typing import Dict, Union, Any, Optional

import requests
from bs4 import BeautifulSoup

__all__ = ["CroatianHolidays", "CroatianHolidaysError", "InvalidYearError",
           "DateFormatError", "NetworkError", "ParseError", "SaveError"]
__version__ = "0.1.4"

logger = logging.getLogger(__name__)
# Don’t spam users unless they opt-in to logging.
logger.addHandler(logging.NullHandler())


class CroatianHolidaysError(Exception):
    """Base exception for this package."""


class InvalidYearError(CroatianHolidaysError):
    """Year is out of supported Gregorian range."""


class DateFormatError(CroatianHolidaysError):
    """Failed to parse or format a date string."""


class NetworkError(CroatianHolidaysError):
    """Networking/HTTP issues when fetching data from the web."""


class ParseError(CroatianHolidaysError):
    """Content structure on the target page didn’t match expectations."""


class SaveError(CroatianHolidaysError):
    """Persisting data to disk failed."""


class CroatianHolidays:
    """
    Utilities for Croatian public holidays.

    Notes:
        - Easter and Corpus Christi are calculated algorithmically.
        - Other holidays are fixed-date for the given year.
        - All date strings are formatted as 'dd. mm. yyyy.' (note the trailing dot).
    """

    def __init__(self) -> None:
        self.NOW: datetime.datetime = datetime.datetime.now()
        self.CURRENT_YEAR: int = self.NOW.year
        self.days_map: Dict[str, str] = {
            "Monday": "Ponedjeljak",
            "Tuesday": "Utorak",
            "Wednesday": "Srijeda",
            "Thursday": "Četvrtak",
            "Friday": "Petak",
            "Saturday": "Subota",
            "Sunday": "Nedjelja",
        }

    # --------------------- Some validation Helpers ---------------------
    def _ensure_bool(self, name: str, value: Any) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"'{name}' must be bool, got {type(value).__name__}")

    def _ensure_year(self, year: int) -> None:
        if not isinstance(year, int):
            raise TypeError(f"'year' must be int, got {type(year).__name__}")
        # Gregorian calendar adopted 1582; computus below is valid for >= 1583
        if year < 1583 or year > 4099:
            raise InvalidYearError(
                f"Year {year} is out of supported range [1583..4099] for the algorithm."
            )

    @staticmethod
    def _as_date(dt: Union[str, datetime.date, datetime.datetime], fmt: str) -> datetime.date:
        if isinstance(dt, datetime.datetime):
            return dt.date()
        if isinstance(dt, datetime.date):
            return dt
        if isinstance(dt, str):
            try:
                return datetime.datetime.strptime(dt, fmt).date()
            except Exception as e:
                raise DateFormatError(f"Failed to parse date string '{dt}' with format '{fmt}'.") from e
        raise TypeError(f"Unsupported type for date: {type(dt).__name__}")

    # --------------------- Public API ---------------------

    def getDayFromDate(
        self,
        date: Union[str, datetime.date, datetime.datetime],
        dateformat: str = "%d. %m. %Y.",
        lang: str = "hr",
    ) -> str:
        """
        Return the weekday name for the given date.
        Args:
            date: string in 'dateformat', or a date/datetime object.
            dateformat: strptime format when 'date' is a string.
            lang: 'hr' for Croatian (default) or 'en' for English.
        """
        if lang not in {"hr", "en"}:
            raise ValueError("Parameter 'lang' must be 'hr' or 'en'.")

        try:
            date_obj = self._as_date(date, dateformat)
            day_en = date_obj.strftime("%A")
            if lang == "en":
                return day_en
            # Fallback to English name if mapping missing (shouldn’t happen)
            return self.days_map.get(day_en, day_en)
        except CroatianHolidaysError:
            raise
        except Exception as e:
            raise DateFormatError(f"Failed to derive weekday from '{date}'.") from e

    @staticmethod
    def getEasterDate(year: int) -> datetime.date:
        """Meeus/Jones/Butcher Gregorian algorithm for Easter Sunday."""
        # Validate here as it’s a staticmethod commonly used externally
        if not isinstance(year, int):
            raise TypeError(f"'year' must be int, got {type(year).__name__}")
        if year < 1583 or year > 4099:
            raise InvalidYearError(
                f"Year {year} is out of supported range [1583..4099] for the computus algorithm."
            )

        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return datetime.date(year, month, day)

    def getCorpusChristiDate(self, year: int) -> datetime.date:
        """Corpus Christi is 60 days after Easter Sunday."""
        self._ensure_year(year)
        return self.getEasterDate(year) + datetime.timedelta(days=60)

    def getHolidays(
        self, year: int, showdays: bool = False, prettyprint: bool = False
    ) -> Union[Dict[str, Any], str]:
        """
        Return Croatian public holidays for a given year.

        If showdays=True, values include 'name' and 'day_of_week'.
        If prettyprint=True, returns a pretty JSON string instead of dict.
        """
        self._ensure_year(year)
        self._ensure_bool("showdays", showdays)
        self._ensure_bool("prettyprint", prettyprint)

        try:
            easter_dt = self.getEasterDate(year)
            easter = easter_dt.strftime("%d. %m.")
            easter_mon = (easter_dt + datetime.timedelta(days=1)).strftime("%d. %m.")
            corpus_christi = self.getCorpusChristiDate(year).strftime("%d. %m.")

            holidays_dict: Dict[str, str] = {
                f"01. 01. {year}.": "Nova godina",
                f"06. 01. {year}.": "Bogojavljenje ili Sveta tri kralja",
                f"{easter} {year}.": "Uskrs",
                f"{easter_mon} {year}.": "Uskrsni ponedjeljak",
                f"01. 05. {year}.": "Praznik rada",
                f"30. 05. {year}.": "Dan državnosti",
                f"{corpus_christi} {year}.": "Tijelovo",
                f"22. 06. {year}.": "Dan antifašističke borbe",
                f"05. 08. {year}.": "Dan pobjede i domovinske zahvalnosti i Dan hrvatskih branitelja",
                f"15. 08. {year}.": "Velika Gospa",
                f"01. 11. {year}.": "Dan svih svetih",
                f"18. 11. {year}.": "Dan sjećanja na žrtve Domovinskog rata",
                f"25. 12. {year}.": "Božić",
                f"26. 12. {year}.": "Sveti Stjepan",
            }

            if not showdays:
                return self.prettyPrint(holidays_dict) if prettyprint else holidays_dict

            holidays: Dict[str, Dict[str, str]] = {}
            for date_str, holiday_name in holidays_dict.items():
                try:
                    day = self.getDayFromDate(date_str, lang="hr")
                except DateFormatError as e:
                    # Attach context but keep processing others
                    logger.warning("Skipping date with parsing error: %s (%s)", date_str, e)
                    continue
                holidays[date_str] = {"name": holiday_name, "day_of_week": day}

            return self.prettyPrint(holidays) if prettyprint else holidays

        except CroatianHolidaysError:
            raise
        except Exception as e:
            raise CroatianHolidaysError("Unexpected error while assembling holidays.") from e

    def getHolidaysFromWeb(
        self,
        base_url: str = "https://neradni-dani.com/neradni-dani-blagdani-praznici-hrvatskoj.php",
        prettyPrint: bool = False,
        timeout: float = 10.0,
        session: Optional[requests.Session] = None,
        user_agent: Optional[str] = None,
    ) -> Union[Dict[str, str], str]:
        """
        Download a webpage and parse Croatian holidays.

        Returns:
            dict or pretty-printed JSON string.

        Raises:
            NetworkError: for HTTP/connection/timeout issues.
            ParseError: when expected structure is missing.
        """
        self._ensure_bool("prettyPrint", prettyPrint)

        headers = {
            "User-Agent": user_agent
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }

        sess = session or requests.Session()
        try:
            resp = sess.get(base_url, headers=headers, timeout=timeout)
            resp.raise_for_status()
        except (requests.Timeout, requests.ConnectionError) as e:
            raise NetworkError(f"Failed to fetch '{base_url}': {e}") from e
        except requests.HTTPError as e:
            code = getattr(e.response, "status_code", "unknown")
            raise NetworkError(f"HTTP {code} while fetching '{base_url}'.") from e
        except Exception as e:
            raise NetworkError(f"Unexpected networking error for '{base_url}': {e}") from e

        soup = BeautifulSoup(resp.text, "html.parser")

        # Be defensive about the structure.
        table = soup.find("table", class_="tablica")
        if table is None:
            # Try a looser fallback before giving up
            table = soup.find("table")
            if table is None:
                raise ParseError("Could not find a holidays table on the page.")

        rows = table.find_all("tr")
        if not rows:
            raise ParseError("No rows found in the holidays table.")

        result: Dict[str, str] = {}
        for row in rows:
            # Skip header rows if present
            if row.find("th"):
                continue
            cols = row.find_all("td")
            # Expecting 3 columns: day (text), date, name
            if len(cols) >= 3:
                datum = cols[1].get_text(strip=True)
                naziv = cols[2].get_text(strip=True)
                if datum and naziv:
                    result[datum] = naziv

        if not result:
            raise ParseError("Parsed table but did not extract any holidays.")

        return self.prettyPrint(result) if prettyPrint else result

    def upcomingHolidays(
        self,
        date: datetime.datetime,
        showdays: bool = False,
        prettyPrint: bool = False,
    ) -> Dict[str, Any]:
        """
        Return upcoming holidays after the specified datetime (current year only).
        """
        if not isinstance(date, datetime.datetime):
            raise TypeError("'date' must be a datetime.datetime instance.")
        self._ensure_bool("showdays", showdays)
        self._ensure_bool("prettyPrint", prettyPrint)

        upcoming: Dict[str, Any] = {}
        try:
            holiday_map = self.getHolidays(self.CURRENT_YEAR, showdays=showdays)
        except CroatianHolidaysError:
            raise
        for d, holiday in holiday_map.items():
            try:
                holiday_dt = datetime.datetime.strptime(d, "%d. %m. %Y.")
            except Exception as e:
                logger.warning("Skipping malformed holiday date '%s': %s", d, e)
                continue
            if holiday_dt > date:
                upcoming[d] = holiday

        return self.prettyPrint(upcoming) if prettyPrint else upcoming

    def isHoliday(self) -> bool:
        """Return True if *today* is a holiday in the current year."""
        today = self.NOW.strftime("%d. %m. %Y.")
        try:
            holidays_dict = self.getHolidays(self.CURRENT_YEAR)
        except CroatianHolidaysError:
            # If holiday generation failed, conservatively report False
            logger.exception("Failed to compute holidays for current year.")
            return False
        return today in holidays_dict

    def getHolidaysBetweenDates(
        self,
        start_date: Union[str, datetime.date, datetime.datetime],
        end_date: Union[str, datetime.date, datetime.datetime],
        showdays: bool = False,
        prettyPrint: bool = False,
        dateformat: str = "%d. %m. %Y.",
    ) -> Dict[str, Any]:
        """
        Return holidays between two inclusive dates.
        """
        self._ensure_bool("showdays", showdays)
        self._ensure_bool("prettyPrint", prettyPrint)

        start = self._as_date(start_date, dateformat)
        end = self._as_date(end_date, dateformat)
        if start > end:
            raise ValueError("start_date must be <= end_date.")

        # Pull distinct years only once
        years = range(start.year, end.year + 1)

        out: Dict[str, Any] = {}
        for y in years:
            try:
                holiday_map = self.getHolidays(y, showdays=showdays)
            except CroatianHolidaysError:
                raise
            for d, h in holiday_map.items():
                try:
                    d_date = datetime.datetime.strptime(d, "%d. %m. %Y.").date()
                except Exception as e:
                    logger.warning("Skipping malformed holiday date '%s': %s", d, e)
                    continue
                if start <= d_date <= end:
                    out[d] = h

        return self.prettyPrint(out) if prettyPrint else out

    # --------------------- Some utilities ---------------------

    @staticmethod
    def prettyPrint(json_data: Dict[str, Any]) -> str:
        """Return a pretty-printed JSON string (UTF-8, no ASCII escapes)."""
        if not isinstance(json_data, dict):
            raise TypeError(f"'json_data' must be dict, got {type(json_data).__name__}")
        try:
            return json.dumps(json_data, indent=4, ensure_ascii=False)
        except Exception as e:
            raise CroatianHolidaysError("Failed to pretty-print JSON data.") from e

    @staticmethod
    def saveToJson(data: Dict[str, Any], filename: str, encoding: str = "utf-8") -> None:
        """
        Save a dictionary to a JSON file.

        Raises:
            SaveError on failure.
        """
        if not isinstance(data, dict):
            raise TypeError(f"'data' must be dict, got {type(data).__name__}")
        if not isinstance(filename, str):
            raise TypeError(f"'filename' must be str, got {type(filename).__name__}")
        try:
            with open(filename, "w", encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError as e:
            raise SaveError(f"Failed to write to '{filename}': {e}") from e
        except Exception as e:
            raise SaveError(f"Unexpected error saving JSON to '{filename}': {e}") from e


if __name__ == "__main__":
    ch = CroatianHolidays()
    print(f"Is today a holiday? -> {ch.isHoliday()}")
    print(ch.upcomingHolidays(date=datetime.datetime.now(), showdays=True, prettyPrint=True))
    print(ch.getHolidaysBetweenDates(
        datetime.datetime.now().date(),
        datetime.date(datetime.datetime.now().year, 11, 20),
        showdays=True,
        prettyPrint=True
    ))
    hol_2025 = ch.getHolidays(2025, showdays=True)
    print(hol_2025["01. 05. 2025."].get("day_of_week"))
