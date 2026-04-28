"""Script de verificación reproducible para conectar a Power BI Desktop usando pyadomd.

Este script intenta:
- localizar la carpeta `AnalysisServicesWorkspaces` y el puerto XMLA
- cargar las DLLs de `vendor/adomd` vía `Assembly.LoadFrom`
- importar `pyadomd` y ejecutar una consulta DAX simple

Imprime un JSON con el resultado.
"""
import os
import json
import traceback

ROOT = os.path.dirname(os.path.dirname(__file__))
# Try both the package-local vendor and the workspace-level vendor
VENDOR_CANDIDATES = [
    os.path.abspath(os.path.join(ROOT, 'vendor', 'adomd')),
    os.path.abspath(os.path.join(ROOT, '..', 'vendor', 'adomd')),
]

def find_vendor_dir():
    for d in VENDOR_CANDIDATES:
        if os.path.isdir(d):
            return d
    return None

VENDOR_ADOMD = find_vendor_dir()

def discover_local_instance() -> tuple[str, str] | None:
    local_app = os.getenv('LOCALAPPDATA')
    if not local_app:
        return None
    root = os.path.join(local_app, 'Microsoft', 'Power BI Desktop', 'AnalysisServicesWorkspaces')
    if not os.path.isdir(root):
        return None
    # pick most recent workspace
    candidates = []
    for dirpath, dirs, _ in os.walk(root):
        if 'Data' in dirs:
            port_file = os.path.join(dirpath, 'Data', 'msmdsrv.port.txt')
            if os.path.exists(port_file):
                try:
                    with open(port_file, 'r', encoding='utf-8', errors='ignore') as f:
                        raw = f.read().replace('\x00','')
                    import re
                    m = re.search(r"(\d+)", raw)
                    if m:
                        port = m.group(1)
                        workspace = os.path.basename(dirpath)
                        candidates.append((port, workspace))
                except Exception:
                    continue
    return candidates[0] if candidates else None

def load_vendor_dlls():
    loaded = []
    if not os.path.isdir(VENDOR_ADOMD):
        return loaded
    try:
        import clr  # type: ignore
        from System.Reflection import Assembly  # type: ignore
        for fname in os.listdir(VENDOR_ADOMD):
            if fname.lower().endswith('.dll'):
                path = os.path.join(VENDOR_ADOMD, fname)
                try:
                    Assembly.LoadFrom(path)
                    loaded.append(path)
                except Exception:
                    # ignore but log
                    loaded.append({'failed': path})
    except Exception:
        # fallback: try ctypes load of main dll
        try:
            import ctypes
            adomd_dll = os.path.join(VENDOR_ADOMD, 'Microsoft.AnalysisServices.AdomdClient.dll')
            if os.path.exists(adomd_dll):
                ctypes.WinDLL(adomd_dll)
                loaded.append(adomd_dll)
        except Exception:
            pass
    return loaded

def main():
    out = { 'ok': False }
    try:
        inst = discover_local_instance()
        out['discovered'] = bool(inst)
        if not inst:
            print(json.dumps(out, ensure_ascii=False))
            return 2

        assert inst is not None
        port, workspace = inst  # type: ignore
        out['port'] = port
        out['workspace'] = workspace

        loaded = load_vendor_dlls()
        out['vendor_loaded'] = loaded

        # try import and connect
        try:
            from pyadomd import Pyadomd  # type: ignore
        except Exception as e:
            out['error_import_pyadomd'] = str(e)
            print(json.dumps(out, ensure_ascii=False))
            return 3

        cs = f"Provider=MSOLAP;Data Source=localhost:{port}"
        out['connection_string'] = cs
        try:
            with Pyadomd(cs) as conn:
                cur = conn.cursor()
                cur.execute("SELECT TOP 3 [Name] FROM $SYSTEM.TMSCHEMA_TABLES")
                rows = cur.fetchall()
                out['tables_sample'] = [r[0] for r in rows if r]
                out['ok'] = True
        except Exception as e:
            out['error_connect'] = str(e)
            # include traceback small
            out['traceback'] = traceback.format_exc(limit=3)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 4

        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e), 'traceback': traceback.format_exc()}, ensure_ascii=False, indent=2))
        return 99

if __name__ == '__main__':
    raise SystemExit(main())
