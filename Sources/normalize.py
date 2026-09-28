"""Text preparation for speech; never changes stored note fields."""
import re
import unicodedata
from datetime import date
from html.parser import HTMLParser
from num2words import num2words
from normalize_russian import normalize_ru

SOUND = re.compile(r'\[sound:[^\]\r\n]+\]', re.I)
MONTHS = {
    'de': 'Januar Februar März April Mai Juni Juli August September Oktober November Dezember'.split(),
    'fr': 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split(),
}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag in ('br', 'p', 'div', 'li') and not self.hidden:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li') and not self.hidden:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def clean_text(field, pause_blocks=False):
    parser = PlainText()
    parser.feed(unicodedata.normalize('NFC', SOUND.sub('', field)).replace('\u00ad', ''))
    text = ''.join(parser.parts)
    if pause_blocks:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = ' '.join(line if re.search(r'[.!?:;…]$', line) else line + '.' for line in lines)
    text = re.sub(r'\{\{c\d+::(.*?)(?:::[^{}]*)?\}\}', r'\1', text)
    return re.sub(r'\s+', ' ', text).strip()


def number(value, language):
    return num2words(int(value), lang=language)


def ordinal_de(value, ending=''):
    return num2words(int(value), lang='de', to='ordinal') + ending


def normalize(text, language):
    if language == 'ru':
        return normalize_ru(text)
    if language in ('en', 'es'):
        return normalize_en_es(text, language)
    if language not in MONTHS:
        raise ValueError('Unsupported language')
    text = re.sub(r'\s+', ' ', text).strip()
    if language == 'fr':
        # French phonemization otherwise softens G and loses the final consonant.
        text = re.sub(r'\bGit\b', 'guite', text)
    else:
        # Keep common German study-card abbreviations explicit before generic number expansion.
        text = re.sub(r'\b3MM\b', 'drei M M', text)
        text = re.sub(r'\b(\d+)er\b', lambda m: number(m[1], language) + 'er', text)
        text = re.sub(r'\bCO2\b', 'C O zwei', text)
        text = re.sub(r'\b([A-Z])2([A-Z])\b', r'\1 zwei \2', text)
    # Postal codes are identifiers, so preserve every digit, including zeros.
    text = re.sub(
        r'((?:Postleitzahl|code postal)\D{0,20})(\d{5})(?!\d)',
        lambda m: m[1] + ' '.join(number(d, language) for d in m[2]),
        text, flags=re.I,
    )
    text = re.sub(r'\b([ABC])([12])\b',
                  lambda m: m[1] + ' ' + number(m[2], language), text)

    def clock(match):
        hour, minute = int(match[1]), int(match[2])
        if hour > 23 or minute > 59:
            raise ValueError('Invalid time')
        if language == 'de':
            hours = ('ein' if hour == 1 else number(hour, language)) + ' Uhr'
        else:
            hours = 'une heure' if hour == 1 else number(hour, language) + ' heures'
        return hours + (' ' + number(minute, language) if minute else '')

    text = re.sub(r'\b(\d{1,2}):(\d{2})(?:\s*Uhr)?\b', clock, text)
    if language == 'de':
        text = re.sub(r'\b(\d{1,2})\.(\d{2})\s*Uhr\b', clock, text)
    # Thousands separators must be removed before recognizing numeric dates.
    if language == 'de':
        text = re.sub(r'\b\d{1,3}(?:\.\d{3})+\b', lambda m: m[0].replace('.', ''), text)
    else:
        text = re.sub(r'\b\d{1,3}(?: \d{3})+\b', lambda m: m[0].replace(' ', ''), text)

    def numeric_date(match):
        day, month = int(match[1]), int(match[2])
        year = int(match[3]) if match[3] else None
        date(year or 2000, month, day)
        before = text[:match.start()]
        if language == 'de':
            oblique = re.search(r'\b(am|vom|zum|ab|bis|den)\s*$', before, re.I)
            spoken_day = ordinal_de(day, 'n' if oblique else 'r')
        else:
            spoken_day = 'premier' if day == 1 else number(day, language)
        result = spoken_day + ' ' + MONTHS[language][month - 1]
        return result + (' ' + number(year, language) if year else '')

    text = re.sub(r'\b(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?(?!\d|\.\d)', numeric_date, text)
    if language == 'de':
        months = '|'.join(MONTHS['de'])
        text = re.sub(r'\b(vom|am|ab)\s+(\d{1,2})\.\s+bis\s+(\d{1,2})\.\s+(' + months + r')\b',
                      lambda m: m[1] + ' ' + ordinal_de(m[2], 'n') + ' bis ' + ordinal_de(m[3], 'n') + ' ' + m[4], text, flags=re.I)
        def named_date(match):
            before = text[:match.start()]
            oblique = re.search(r'\b(am|vom|zum|ab|bis|den)\s*$', before, re.I)
            return ordinal_de(match[1], 'n' if oblique else 'r') + ' ' + match[2]
        text = re.sub(r'\b(\d{1,2})\.\s*(' + months + r')\b', named_date, text, flags=re.I)
        text = re.sub(r'\b(\d+)\.\s+(?=[A-ZÄÖÜ])', lambda m: ordinal_de(m[1]) + ' ', text)
    else:
        text = re.sub(r'\b1(?:er)?\s+(?=' + '|'.join(MONTHS['fr']) + r'\b)', 'premier ', text)

    amount_pattern = r'\d+(?:,\d{1,2})?'
    text = re.sub(r'([€$])\s*(' + amount_pattern + r')(?!\d)', r'\2 \1', text)
    text = re.sub(r'(\d+)\s*([€$])\s*,\s*[-–]', r'\1 \2', text)

    def money(match):
        whole, _, cents = match[1].partition(',')
        amount = int(whole)
        value = ('ein' if amount == 1 and language == 'de' else number(amount, language))
        unit = 'Euro' if match[2] == '€' else 'Dollar'
        if language == 'fr':
            unit = ('euro' if match[2] == '€' else 'dollar') + ('s' if amount > 1 else '')
        value += ' ' + unit
        fraction = int(cents.ljust(2, '0')) if cents else 0
        if fraction:
            value += ' ' + ('ein' if fraction == 1 and language == 'de' else number(fraction, language))
            value += (' Cent' if language == 'de' else (' centime' if fraction == 1 else ' centimes'))
        return value

    text = re.sub(r'\b(' + amount_pattern + r')\s*([€$])', money, text)
    text = text.replace('%', ' Prozent ' if language == 'de' else ' pour cent ')
    text = re.sub(r'(?<=\d)[–−-](?=\d)', ' bis ' if language == 'de' else ' à ', text)
    text = re.sub(r'\b(\d+),(\d+)\b',
                  lambda m: number(m[1], language) + (' Komma ' if language == 'de' else ' virgule ') + ' '.join(number(d, language) for d in m[2]), text)
    units = {'de': {'kg': 'Kilogramm', 'km': 'Kilometer', 'cm': 'Zentimeter', 'mm': 'Millimeter'},
             'fr': {'kg': 'kilogrammes', 'km': 'kilomètres', 'cm': 'centimètres', 'mm': 'millimètres'}}
    for short, expanded in units[language].items():
        text = re.sub(r'\b' + short + r'\b', expanded, text)
    text = re.sub(r'(?<!\w)\d+(?!\w)', lambda m: number(m[0], language), text)
    if language == 'de':
        text = re.sub(r'\beins (?=Uhr|Euro|Dollar|Prozent|Kilogramm|Kilometer)', 'ein ', text)
        text = re.sub(r'\bmind\.', 'mindestens', text)
    if re.search(r'\d', text):
        raise ValueError('Unresolved number or identifier')
    return re.sub(r'\s+', ' ', text).strip()


def normalize_en_es(text, language):
    """Expand unambiguous numeric forms; reject ambiguous numeric dates."""
    text = re.sub(r'\s+', ' ', text).strip()
    if re.search(r'\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b', text):
        raise ValueError('Ambiguous numeric date; use a spelled-out month')
    text = re.sub(r'\b([ABC])([12])\b', lambda m: m[1] + ' ' + number(m[2], language), text)
    def clock(match):
        hour, minute = int(match[1]), int(match[2])
        if hour > 23 or minute > 59:
            raise ValueError('Invalid time')
        if language == 'en':
            suffix = " o'clock" if minute == 0 else (' oh ' if minute < 10 else ' ') + number(minute, language)
            return number(hour, language) + suffix
        return ('una' if hour == 1 else number(hour, language)) + (' en punto' if minute == 0 else ' y ' + number(minute, language))
    text = re.sub(r'\b(\d{1,2}):(\d{2})\b', clock, text)
    # Normalize thousands only when the full grouping is unambiguous.
    thousands = r'\b\d{1,3}(?:,\d{3})+\b' if language == 'en' else r'\b\d{1,3}(?:\.\d{3})+\b'
    separator = ',' if language == 'en' else '.'
    text = re.sub(thousands, lambda m: m[0].replace(separator, ''), text)
    decimal = '.' if language == 'en' else ','
    amount = r'\d+(?:' + re.escape(decimal) + r'\d{1,2})?'
    text = re.sub(r'([$€£])\s*(' + amount + r')', r'\2 \1', text)
    def money(match):
        whole, _, cents = match[1].partition(decimal)
        units = {'en': {'$':'dollars', '€':'euros', '£':'pounds'}, 'es': {'$':'dólares', '€':'euros', '£':'libras'}}
        unit = units[language][match[2]]
        if int(whole) == 1:
            unit = {'dollars':'dollar','euros':'euro','pounds':'pound','dólares':'dólar','libras':'libra'}[unit]
        main = ('un' if language == 'es' and int(whole) == 1 else number(whole, language)) + ' ' + unit
        fraction = int(cents.ljust(2, '0')) if cents else 0
        if fraction:
            main += (' and ' if language == 'en' else ' con ') + number(fraction, language)
            main += (' cent' if fraction == 1 else ' cents') if language == 'en' else (' céntimo' if fraction == 1 else ' céntimos')
        return main
    text = re.sub(r'\b(' + amount + r')\s*([$€£])', money, text)
    text = text.replace('%', ' percent ' if language == 'en' else ' por ciento ')
    text = re.sub(r'(?<=\d)[–−-](?=\d)', ' to ' if language == 'en' else ' a ', text)
    text = re.sub(r'\b(\d+)' + re.escape(decimal) + r'(\d+)\b', lambda m: number(m[1], language) + (' point ' if language == 'en' else ' coma ') + ' '.join(number(d, language) for d in m[2]), text)
    text = re.sub(r'(?<!\w)\d+(?!\w)', lambda m: number(m[0], language), text)
    if re.search(r'\d', text):
        raise ValueError('Unresolved number or identifier')
    return re.sub(r'\s+', ' ', text).strip()
