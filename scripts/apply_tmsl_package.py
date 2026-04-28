import json
from pathlib import Path
from src.powerbi_client import PowerBIClient

pkg_path = Path(__file__).resolve().parents[1] / 'artifacts' / 'tmsl_package.json'
if not pkg_path.exists():
    raise SystemExit(f'No se encontró {pkg_path}')

pkg = json.loads(pkg_path.read_text(encoding='utf-8'))
client = PowerBIClient()
print('Refrescando conexión...')
print(client.refresh_connection())

results = []
for item in pkg.get('items', []):
    if item.get('type') == 'create_measure':
        tmsl = item.get('tmsl')
        print('Aplicando create_measure para', item.get('measure_name'))
        resp = client.apply_tmsl(tmsl, catalog='')
        results.append({'item': item, 'resp': resp})
    else:
        results.append({'item': item, 'resp': {'status': 'skipped', 'reason': 'unknown type'}})

print(json.dumps(results, indent=2, ensure_ascii=False))
