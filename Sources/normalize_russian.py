"""Normalize Russian numbers without silently dropping unsupported text."""
import re
from datetime import date
from decimal import Decimal
from num2words import num2words

MONTHS = 'января февраля марта апреля мая июня июля августа сентября октября ноября декабря'.split()


def normalize_ru(text):
    def full_date(match):
        day, month, year = map(int, match.groups())
        date(year, month, day)
        return (num2words(day, lang='ru', to='ordinal', gender='n') + ' ' + MONTHS[month - 1] + ' ' +
                num2words(year, lang='ru', to='ordinal', case='g') + ' года')

    def clock(match):
        hours, minutes = map(int, match.groups())
        if hours > 23 or minutes > 59:
            raise ValueError('Invalid Russian time')
        return num2words(hours, lang='ru') + ' ' + num2words(minutes, lang='ru', gender='f')

    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', full_date, text)
    text = re.sub(r'\b(\d{1,2}):(\d{2})\b', clock, text)
    text = re.sub(r'(?<=\d)[ \u00a0](?=\d{3}(?:\D|$))', '', text)
    text = re.sub(r'(?<!\w)(\d+(?:[.,]\d{1,2})?)\s*(?:₽|руб\.?)(?!\w)',
                  lambda m: num2words(Decimal(m[1].replace(',', '.')), lang='ru', to='currency', currency='RUB'), text)
    text = re.sub(r'(?<!\w)(\d+)\s*%', lambda m: num2words(int(m[1]), lang='ru') + ' ' +
                  ('процент' if int(m[1]) % 10 == 1 and int(m[1]) % 100 != 11 else
                   'процента' if int(m[1]) % 10 in (2, 3, 4) and int(m[1]) % 100 not in (12, 13, 14) else 'процентов'), text)
    text = re.sub(r'(?<=\d)[–−-](?=\d)', ' — ', text)
    text = re.sub(r'(?<!\w)-?(?:\d+[.,]\d+|\d+)(?!\w)',
                  lambda m: num2words(Decimal(m[0].replace(',', '.')), lang='ru'), text)
    # Silero may omit unknown characters: reject them before generating any audio.
    if re.search(r'[^А-Яа-яЁё\s.,!?…;:—–\-()\"\x27«»+]', text):
        raise ValueError('Unsupported Russian text; spell out symbols and foreign words')
    return text
