"""Poll de Power BI Desktop hasta que el modelo esté accesible.

El script intenta en bucle (espera configurable) ejecutar consultas $SYSTEM
para obtener tablas y medidas. Termina cuando detecta al menos una tabla
o medida, o cuando supera `max_attempts`.
"""
import time
import os
import json
import traceback

CS_BASE = os.getenv('POWERBI_CONN', 'Provider=MSOLAP;Data Source=localhost:24823')
SLEEP = int(os.getenv('POLL_SLEEP', '5'))
MAX_ATTEMPTS = int(os.getenv('POLL_MAX_ATTEMPTS', '60'))  # ~5 minutes default

def try_fetch():
    from pyadomd import Pyadomd  # type: ignore
    out = {'tables': [], 'measures': [], 'cols': []}
    try:
        with Pyadomd(CS_BASE) as conn:
            cur = conn.cursor()
            try:
                cur.execute('SELECT * FROM $SYSTEM.TMSCHEMA_TABLES')
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchall()
                out['cols'] = cols
                out['tables'] = [r[cols.index('Name')] for r in rows if 'Name' in cols]
            except Exception:
                pass

            try:
                cur.execute('SELECT * FROM $SYSTEM.TMSCHEMA_MEASURES')
                mcols = [c[0] for c in cur.description] if cur.description else []
                mrows = cur.fetchall()
                out['measures'] = [r[mcols.index('Name')] for r in mrows if 'Name' in mcols]
            except Exception:
                pass
    except Exception as e:
        out['error'] = str(e)
        out['trace'] = traceback.format_exc(limit=2)
    return out

def main():
    attempt = 0
    print('Polling Power BI model (conn=%s) every %ds (max %s attempts)' % (CS_BASE, SLEEP, MAX_ATTEMPTS or '∞'))
    while True:
        attempt += 1
        print(f'Attempt {attempt}...')
        res = try_fetch()
        tables = res.get('tables') or []
        measures = res.get('measures') or []
        if tables or measures:
            print('Model accessible!')
            print('Tables:', len(tables))
            print('Measures:', len(measures))
            print(json.dumps({'tables': tables[:50], 'measures': measures[:50]}, ensure_ascii=False, indent=2))
            return 0

        if MAX_ATTEMPTS and attempt >= MAX_ATTEMPTS:
            print('Max attempts reached, giving up.')
            print('Last error:', res.get('error'))
            return 2

        time.sleep(SLEEP)

if __name__ == '__main__':
    raise SystemExit(main())
