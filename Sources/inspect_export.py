"""Read deck and field choices from an isolated export snapshot."""
import argparse
import json
import sqlite3
import tempfile
from pathlib import Path
from collection import extract_collection


def inspect(source):
    with tempfile.TemporaryDirectory(prefix='anki-inspect-') as folder:
        database = Path(folder) / 'collection.sqlite3'
        extract_collection(source, database)
        connection = sqlite3.connect(database)
        try:
            decks = sorted({row[0].replace('\x1f', '::') for row in connection.execute('select name from decks')})
            fields = sorted({row[0] for row in connection.execute('select name from fields')})
            return {'decks': decks, 'fields': fields}
        finally:
            connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.source), ensure_ascii=False))
    except Exception as error:
        print(json.dumps({'error': type(error).__name__}))
        raise SystemExit(1)
