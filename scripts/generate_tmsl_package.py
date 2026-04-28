import os
import json
from pathlib import Path
from src.powerbi_client import PowerBIClient

out_root = Path(__file__).resolve().parents[1] / "artifacts"
out_root.mkdir(parents=True, exist_ok=True)

c = PowerBIClient()
print('Refrescando conexión...')
print(c.refresh_connection())

# Ejemplo: generar tmsl para la medida Copilot_Test_Measure
table = 'superstore_procesado'
measure_name = 'Copilot_Test_Measure'
dax = '1'

payload = c.generate_tmsl_create_measure(table, measure_name, dax)

pkg = {
    'generated_by': 'powerbi-mcp-server',
    'items': [
        {
            'type': 'create_measure',
            'table': table,
            'measure_name': measure_name,
            'dax': dax,
            'tmsl': payload
        }
    ]
}

out_file = out_root / 'tmsl_package.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(pkg, f, ensure_ascii=False, indent=2)

print('Escrito paquete TMSL en:', out_file)

# Crear instrucciones rápidas
instr = out_root / 'TMSL_APPLY_INSTRUCTIONS.md'
if not instr.exists():
    instr.write_text(
        """# Instrucciones para aplicar TMSL (Tabular Editor / SSMS)

Pasos recomendados para aplicar el paquete TMSL generado (`tmsl_package.json`):

1. Abrir Tabular Editor (preferible) o SQL Server Management Studio (SSMS).

2. En Tabular Editor:
   - Conéctate a `localhost:<port>` (el puerto XMLA mostrado en `powerbi-mcp-server`).
   - En `File` → `Open` → `Open JSON/TMSL` y carga el contenido del `tmsl` del paquete.
   - Revisa el JSON y aplica (Save/Execute). Tabular Editor requiere que Power BI Desktop permita conexiones externas.

3. En SSMS:
   - `Connect` → `Analysis Services` → `Server name` = `localhost:<port>` y Authentication = Windows Authentication.
   - Right-click sobre la base de datos del workspace (si aparece), `New Query` → seleccionar `XMLA` y pegar el payload SOAP Execute conteniendo el JSON TMSL.
   - Ejecutar. SSMS puede necesitar permisos/admin.

4. Si el endpoint rechaza Execute (conexión cerrada), exporta los objetos (p.ej. medidas) y aplícalos manualmente dentro de Power BI Desktop o Tabular Editor usando la UI.

""",
        encoding='utf-8'
    )
    print('Escritas instrucciones en:', instr)
else:
    print('Instrucciones ya existían en:', instr)
