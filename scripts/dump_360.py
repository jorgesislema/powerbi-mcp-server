import os
import json
import time
from pathlib import Path
from src.powerbi_client import PowerBIClient

out_root = Path(__file__).resolve().parents[1] / "artifacts"
out_root.mkdir(parents=True, exist_ok=True)
subdir = out_root / f"vista_360_{int(time.time())}"
subdir.mkdir(parents=True, exist_ok=True)

c = PowerBIClient()
print("Refrescando conexión local...")
print(c.refresh_connection())

result = {}

# Tables
try:
    tables = c.get_tables()
    result['tables_count'] = len(tables)
    with open(subdir / 'tables.json', 'w', encoding='utf-8') as f:
        json.dump(tables, f, ensure_ascii=False, indent=2, default=str)
    print(f'Escritas {len(tables)} tablas')
except Exception as e:
    print('Error obteniendo tablas:', e)
    tables = []

# For each table get columns and measures
for t in tables:
    name = t.get('Name') or t.get('Table') or str(t.get('ID'))
    safe_name = ''.join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name])
    try:
        cols = c.get_columns(table_name=name)
        with open(subdir / f'columns__{safe_name}.json', 'w', encoding='utf-8') as f:
            json.dump(cols, f, ensure_ascii=False, indent=2, default=str)
        print(f'Columnas para {name}: {len(cols)}')
    except Exception as e:
        print(f'Error columnas {name}:', e)

    try:
        measures = c.get_measures(table_name=name)
        with open(subdir / f'measures__{safe_name}.json', 'w', encoding='utf-8') as f:
            json.dump(measures, f, ensure_ascii=False, indent=2, default=str)
        print(f'Medidas para {name}: {len(measures)}')
    except Exception as e:
        print(f'Error medidas {name}:', e)

# Relationships
try:
    rels = c.get_relationships()
    with open(subdir / 'relationships.json', 'w', encoding='utf-8') as f:
        json.dump(rels, f, ensure_ascii=False, indent=2, default=str)
    print(f'Relationships: {len(rels)}')
except Exception as e:
    print('Error relationships:', e)

# Model info
try:
    info = c.get_model_info()
    with open(subdir / 'model_info.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2, default=str)
    print('Info model escrita')
except Exception as e:
    print('Error model_info:', e)

print('Dump 360 completo en:', subdir)
