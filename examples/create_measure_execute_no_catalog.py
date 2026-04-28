import os
import json
from src.powerbi_client import PowerBIClient

c = PowerBIClient()
print("Refrescando conexión local...")
print(c.refresh_connection())

measure_name = "Copilot_Test_Measure_NoCatalog"

dax_expr = "1"

table_name = "superstore_procesado"

print(f"Generando TMSL para medida en tabla: {table_name}")
tmsl = c.generate_tmsl_create_measure(table_name, measure_name, dax_expr)
print(json.dumps(tmsl, indent=2, ensure_ascii=False))

print("Intentando ejecutar TMSL SIN Catalog header...")
resp = c.apply_tmsl(tmsl, catalog="")
print(json.dumps(resp, indent=2, ensure_ascii=False))
