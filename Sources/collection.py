"""Read an export snapshot and select explicitly requested audio fields."""
import hashlib
import os
import tempfile
import re
import sqlite3
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
import zstandard
from normalize import SOUND, clean_text, normalize


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def extract_collection(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise FileExistsError('Destination already exists')
    descriptor, temporary_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.partial', dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            name = next((n for n in ('collection.anki21b', 'collection.anki21', 'collection.anki2') if n in names), None)
            if name is None:
                raise ValueError('Collection is missing from export')
            with archive.open(name) as src, temporary.open('wb') as dst:
                if name.endswith('21b'):
                    zstandard.ZstdDecompressor().copy_stream(src, dst)
                else:
                    import shutil
                    shutil.copyfileobj(src, dst)
        with temporary.open('rb') as stream:
            if stream.read(16) != b'SQLite format 3\0':
                raise ValueError('Invalid collection database')
        temporary.rename(destination)
    finally:
        temporary.unlink(missing_ok=True)


def field_language(roots, field_name):
    # Mixed deck membership is ambiguous and must be reviewed separately.
    if len(roots) == 1 and roots <= {
        '!Немецкий', 'Deutsch', 'German', 'Немецкий',
        'Umschulung Wörter', 'ПРАВИЛА немецкого',
    } and field_name == 'Front':
        return 'de_front', 'de'
    if len(roots) == 1 and field_name == 'Front':
        if roots <= {'Русский', 'Русский язык', 'Russian', 'Russisch'}:
            return 'ru_front', 'ru'
        if roots <= {'English', 'Englisch', 'Английский'}:
            return 'en_front', 'en'
        if roots <= {'Español', 'Spanish', 'Spanisch', 'Испанский'}:
            return 'es_front', 'es'
    if len(roots) == 1 and roots <= {'Французский', 'Französisch', 'French'}:
        if field_name == 'Front':
            return 'fr_front', 'fr'
        if field_name == 'Back':
            return 'fr_back', 'de'
    return None


def without_cyrillic(text):
    """Keep the foreign-language part of a card when it contains a Russian hint."""
    text = re.sub(r'[А-Яа-яЁё]+(?:[.!?,;:…—–-]*[А-Яа-яЁё]+)*[.!?,;:…]*', ' ', text)
    text = re.sub(r'(^|\s)[—–-]+(?=\s|$)', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def candidates(database, selection=None):
    selection = selection or {'mode': 'existing'}
    connection = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        decks = dict(connection.execute('select id,name from decks'))
        fields = defaultdict(dict)
        for model, order, name in connection.execute('select ntid,ord,name from fields'):
            fields[model][order] = name
        membership = defaultdict(set)
        full_membership = defaultdict(set)
        for note, deck in connection.execute('select nid,case when odid!=0 then odid else did end from cards'):
            membership[note].add(decks[deck].split('\x1f')[0])
            full_membership[note].add(decks[deck].replace('\x1f', '::'))
        counts, records = Counter(), []
        has_tags = any(row[1] == 'tags' for row in connection.execute('pragma table_info(notes)'))
        query = 'select id,mid,flds,' + ('tags' if has_tags else "''") + ' from notes order by id'
        for note, model, values, tags in connection.execute(query):
            selected_deck = selection.get('deck', '')
            in_deck = bool(selected_deck) and all(
                d == selected_deck or d.startswith(selected_deck + '::') for d in full_membership[note]
            ) and bool(full_membership[note])
            for order, value in enumerate(values.split('\x1f')):
                name = fields[model].get(order, '')
                mapping = field_language(membership[note], name)
                mode = selection.get('mode', 'existing')
                target = selection.get('field', '*')
                selected_field = name in ('Front', 'Back') if target == '*' else name == target
                if selected_deck and not in_deck:
                    continue
                if mode == 'existing' and target != '*' and not selected_field:
                    continue
                if mode == 'deck':
                    if not in_deck or not selected_field:
                        continue
                    language = selection.get('back_language', 'de') if name == 'Back' and target == '*' else selection.get('language', 'de')
                    mapping = (language + '_selected', language)
                elif mode == 'tag':
                    if not selected_field:
                        continue
                    # A custom tag is authoritative in tag mode. This also
                    # supports arbitrary deck names (for example
                    # ``Umschulung Wörter``) whose root cannot identify the
                    # language. Only accept an unambiguous configured tag.
                    tag_tokens = set(tags.split())
                    candidates_by_tag = []
                    for candidate_language in ('de', 'fr', 'en', 'es', 'ru'):
                        candidate_tag = selection.get('tag_' + candidate_language, 'sound').strip()
                        if candidate_tag and candidate_tag in tag_tokens:
                            candidates_by_tag.append(candidate_language)
                    if mapping is not None:
                        _, mapped_language = mapping
                        tag_name = selection.get('tag_' + mapped_language, 'sound').strip()
                        if tag_name and tag_name in tag_tokens:
                            language = mapped_language
                        else:
                            continue
                    # A tag can infer the language only for a card's front.
                    # Back fields are often translations, so inferring a
                    # language for them would produce duplicate or wrong audio.
                    elif name == 'Front' and len(candidates_by_tag) == 1:
                        language = candidates_by_tag[0]
                    else:
                        continue
                    mapping = (language + '_tagged', language)
                if mapping is None:
                    continue
                group, language = mapping
                allow_new = mode in ('deck', 'tag')
                if not SOUND.search(value) and not allow_new:
                    counts['without_sound'] += 1
                    continue
                counts[group] += 1
                text = clean_text(value)
                speech_source = clean_text(value, pause_blocks=True)
                if language != 'ru':
                    text = without_cyrillic(text)
                    speech_source = without_cyrillic(speech_source)
                if not text or not re.search(r'[^\W_]', text, re.UNICODE):
                    counts['empty_or_mixed_language'] += 1
                    continue
                records.append({'note_id': note, 'field_order': order, 'field': name, 'group': group,
                                'allow_new': allow_new, 'sound_count': len(SOUND.findall(value)),
                                'language': language, 'original': text, 'speech_source': speech_source,
                                'field_sha256': hashlib.sha256(value.encode()).hexdigest()})
        return records, dict(counts)
    finally:
        connection.close()


CATEGORY_PATTERNS = [
    ('postal', r'55606'), ('full_date', r'\d{2}\.\d{2}\.\d{4}'),
    ('short_date', r'\d{2}\.\d{2}(?![\d.])'), ('time', r'\d{1,2}:\d{2}'),
    ('dot_time', r'\d{1,2}\.\d{2}\s*Uhr'), ('decimal', r'\d+,\d+\s*kg'),
    ('money', r'\d+,\d+\s*€'), ('euro_prefix', r'€\s*\d+'),
    ('percent', r'\d+\s*%'), ('thousands', r'\d\.\d{3}'),
    ('level', r'\bB2\b'), ('range', r'\d+[–-]\d+'),
    ('named_date', r'\d+\.?\s+(?:bis\s+\d+\.\s+|au\s+\d+\s+)?(?:März|Mai|August|mai|août)'),
    ('year', r'\b2026\b'), ('ordinal', r'\d+\.\s+(?:Klasse|Person)'),
    ('number', r'\d'), ('ordinary', r'^[^\d]+$'),
]


def choose_samples(records):
    selected = []
    for group, limit in [('de_front', 16), ('fr_front', 7), ('fr_back', 7)]:
        pool = sorted((r for r in records if r['group'] == group and 3 < len(r['original']) <= 240),
                      key=lambda r: (len(r['original']), r['note_id']))
        if group == 'fr_back':
            translations = {r['note_id']: r for r in pool}
            for front in [r for r in selected if r['group'] == 'fr_front']:
                back = translations.get(front['note_id'])
                if back is None:
                    continue
                try:
                    spoken = normalize(back['speech_source'], back['language'])
                except ValueError:
                    continue
                selected.append(dict(back, category=front['category'], spoken=spoken))
            continue
        used = set()
        def add(record, category):
            key = record['original']
            if key in used:
                return False
            try:
                spoken = normalize(record['speech_source'], record['language'])
            except ValueError:
                return False
            selected.append(dict(record, category=category, spoken=spoken))
            used.add(key)
            return True
        # Always include ordinary speech alongside number-heavy cases.
        ordinary = [r for r in pool if not re.search(r'\d', r['original']) and 35 <= len(r['original']) <= 120]
        for record in ordinary[:2 if group != 'de_front' else 1]:
            add(record, 'ordinary')
        for category, pattern in CATEGORY_PATTERNS:
            if len(used) >= limit:
                break
            category_pool = ordinary if category == 'ordinary' else pool
            for record in category_pool:
                if re.search(pattern, record['original']) and add(record, category):
                    break
        for record in ordinary:
            if len(used) >= limit:
                break
            add(record, 'ordinary')
    return selected
