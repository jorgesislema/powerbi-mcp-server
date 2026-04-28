import os
import json
from src.powerbi_client import PowerBIClient

c = PowerBIClient()
print("Refrescando conexión local...")
print(c.refresh_connection())

# intentar obtener tablas disponibles
try:
    tables = c.get_tables()
except Exception as e:
    print("No se pudieron obtener tablas:", e)
    tables = []

if tables:
    # elegir tabla preferida si existe
    preferred = next((t for t in tables if t.get("Name") == "superstore_procesado"), None)
    table_name = preferred.get("Name") if preferred else tables[0].get("Name")
else:
    table_name = "superstore_procesado"

measure_name = "Copilot_Test_Measure"
# expresión DAX simple: número constante (no depende de columnas)
# Nota: algunas expresiones pueden no ser válidas como medida, pero esto es un ejemplo.
dax_expr = "1"

print(f"Generando TMSL para medida en tabla: {table_name}")
tmsl = c.generate_tmsl_create_measure(table_name, measure_name, dax_expr)
print(json.dumps(tmsl, indent=2, ensure_ascii=False))

# Ejecutar solo si la variable de entorno EXECUTE=1
if os.environ.get("EXECUTE") == "1":
    print("Intentando ejecutar TMSL contra el endpoint XMLA local...")
    resp = c.create_measure(table_name, measure_name, dax_expr, execute=True)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
else:
    print("No se ejecutó el TMSL. Para ejecutar establece EXECUTE=1 y vuelve a correr.")
