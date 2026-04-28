"""Dump model metadata (tables, columns, measures) to artifacts/*.json

Usa la misma detección de instancia que `powerbi_client` y escribe
`artifacts/tables.json`, `artifacts/columns.json`, `artifacts/measures.json`.
"""
import os
import json
import traceback
from datetime import datetime


def safe(o):
    if isinstance(o, datetime):
        return o.isoformat()
    try:
        json.dumps(o)
        return o
    except Exception:
        return str(o)


def find_latest_instance():
    local_app = os.getenv('LOCALAPPDATA')
    if not local_app:
        return None, None
    root = os.path.join(local_app, 'Microsoft', 'Power BI Desktop', 'AnalysisServicesWorkspaces')
    if not os.path.isdir(root):
        return None, None
    latest: tuple[float, str, str] | None = None
    for port_file in (p for p in __import__('pathlib').Path(root).glob('*/Data/msmdsrv.port.txt')):
        try:
            raw = port_file.read_text(encoding='utf-8', errors='ignore').replace('\x00','')
            import re
            m = re.search(r"(\d+)", raw)
            if m:
                port = m.group(1)
                workspace = port_file.parents[1].name
                t = port_file.stat().st_mtime
                if latest is None or t > latest[0]:  # type: ignore[index]
                    latest = (t, port, workspace)
        except Exception:
            continue
    if not latest:
        return None, None
    return latest[1], latest[2]


def load_vendor_dlls():
    # try workspace-local then repo-level vendor
    candidates = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vendor', 'adomd')), os.path.abspath(os.path.join('..', 'vendor', 'adomd'))]
    for vendor in candidates:
        if os.path.isdir(vendor):
            try:
                import clr  # type: ignore
                from System.Reflection import Assembly  # type: ignore
                for f in os.listdir(vendor):
                    if f.lower().endswith('.dll'):
                        try:
                            Assembly.LoadFrom(os.path.join(vendor, f))
                        except Exception:
                            pass
                return vendor
            except Exception:
                try:
                    import ctypes
                    adomd_dll = os.path.join(vendor, 'Microsoft.AnalysisServices.AdomdClient.dll')
                    if os.path.exists(adomd_dll):
                        ctypes.WinDLL(adomd_dll)
                        return vendor
                except Exception:
                    pass
    return None


def query_and_dump(cs, outdir):
    from pyadomd import Pyadomd  # type: ignore
    results = {}
    try:
        with Pyadomd(cs) as conn:
            cur = conn.cursor()
            # tables
            try:
                cur.execute('SELECT * FROM $SYSTEM.TMSCHEMA_TABLES')
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchall()
                results['tables'] = [ {cols[i]: safe(r[i]) for i in range(min(len(cols), len(r)))} for r in rows ]
            except Exception:
                results['tables_error'] = traceback.format_exc()

            # columns
            try:
                cur.execute('SELECT * FROM $SYSTEM.TMSCHEMA_COLUMNS')
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchall()
                results['columns'] = [ {cols[i]: safe(r[i]) for i in range(min(len(cols), len(r)))} for r in rows ]
            except Exception:
                results['columns_error'] = traceback.format_exc()

            # measures
            try:
                cur.execute('SELECT * FROM $SYSTEM.TMSCHEMA_MEASURES')
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchall()
                results['measures'] = [ {cols[i]: safe(r[i]) for i in range(min(len(cols), len(r)))} for r in rows ]
            except Exception:
                results['measures_error'] = traceback.format_exc()

    except Exception:
        results['connection_error'] = traceback.format_exc()

    os.makedirs(outdir, exist_ok=True)
    for key in ('tables', 'columns', 'measures'):
        path = os.path.join(outdir, f"{key}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results.get(key) or {'error': results.get(f"{key}_error")}, f, ensure_ascii=False, indent=2)
    # also dump full results
    with open(os.path.join(outdir, 'full_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    port, workspace = find_latest_instance()
    if not port:
        print('No Power BI local instance found')
        return 2
    vendor = load_vendor_dlls()
    print('vendor loaded:', vendor)
    cs = f"Provider=MSOLAP;Data Source=localhost:{port};Initial Catalog={workspace}"
    outdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts'))
    print('Querying', cs)
    query_and_dump(cs, outdir)
    print('Wrote artifacts to', outdir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
