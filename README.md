# powerbi-mcp-server

Servidor [MCP](https://modelcontextprotocol.io) para inspeccionar y modificar modelos **Power BI** (ADOMD + TOM) desde GitHub Copilot u otro cliente MCP.

![CI](https://github.com/jorgesislema/powerbi-mcp-server/actions/workflows/ci.yml/badge.svg)

---

## Características

| Capacidad | API |
|---|---|
| Ejecutar consultas DAX | `execute_dax(dax)` |
| Listar tablas y columnas | `get_tables()`, `get_columns(table)` |
| Listar y crear medidas | `get_measures()`, `create_measure(...)` |
| Aplicar TMSL | `apply_tmsl(json)` |
| Info del modelo | `get_model_info()` |

---

## Requisitos

- **Python 3.10+** (Windows)
- **Power BI Desktop** abierto (el puerto XMLA se descubre automáticamente)
- DLLs de **ADOMD.NET** y **TOM** en `vendor/` (descarga con el script de instalación)

---

## Instalación rápida (nuevo proyecto)

### Opción A — pip desde GitHub (recomendado)

```powershell
pip install "git+https://github.com/jorgesislema/powerbi-mcp-server.git"
```

> Las DLLs no se incluyen en pip. Ejecuta también `install_adomd.ps1` (ver abajo).

### Opción B — editable local (para desarrollo)

```powershell
git clone https://github.com/jorgesislema/powerbi-mcp-server.git
cd powerbi-mcp-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

---

## Instalar DLLs ADOMD/TOM (una sola vez por máquina)

Las DLLs **no están en git**. El script las descarga desde NuGet:

```powershell
.\scripts\install_adomd.ps1
.\scripts\install_adomd.ps1 -CopyToVenv
```

Resultado:

```
vendor/
  adomd/  <- Microsoft.AnalysisServices.AdomdClient.dll
  tom/    <- Microsoft.AnalysisServices.Tabular.dll (y otros)
```

---

## Uso básico en tu propio proyecto

```python
from src.powerbi_client import PowerBIClient

client = PowerBIClient()
client.connect()

# Consulta DAX
df = client.execute_dax("EVALUATE SUMMARIZE('ventas', 'ventas'[region])")

# Listar medidas
for m in client.get_measures():
    print(m["name"], "->", m["expression"])

# Crear medida nueva (via TOM)
client.create_measure(
    table_name="ventas",
    measure_name="Total Ventas",
    expression="SUM(ventas[importe])",
    execute=False,
)
```

---

## Iniciar el servidor MCP

```powershell
python -m src.server
powerbi-mcp
```

Configura en `.vscode/mcp.json` (no versionado) con la ruta al ejecutable.

---

## Variables de entorno

Copia `.env.example` -> `.env`:

```powershell
Copy-Item .env.example .env
```

| Variable | Descripción |
|---|---|
| `POWERBI_MODE` | `local` (Desktop) o `cloud` (Service) |
| `LOCAL_PORT` | Puerto de PBI Desktop (se autodetecta si vacio) |
| `CLOUD_WORKSPACE_ID` | Solo para modo cloud |
| `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` | Solo para modo cloud |

> `.env` esta excluido en `.gitignore`. Solo `.env.example` se versiona (sin valores reales).

---

## Estructura del repositorio

```
powerbi-mcp-server/
├── src/
│   ├── server.py
│   ├── powerbi_client.py
│   ├── tools.py
│   └── dax_validator.py
├── scripts/
│   ├── install_adomd.ps1
│   └── verify_powerbi_connection.py
├── examples/
├── tests/
├── vendor/                # DLLs locales (excluido de git)
├── .env.example           # Plantilla sin secretos
└── pyproject.toml
```

---

## Desarrollo y tests

```powershell
pytest tests/ -v
python .\scripts\verify_powerbi_connection.py
pip install build
python -m build --wheel
```

---

## Seguridad

- **Nunca** subas a git: `.env`, `vendor/`, `artifacts/`, `.vscode/mcp.json`
- `CLIENT_SECRET` y tokens van en `.env` local o en **GitHub Secrets**
- Las DLLs se reinstalan con `install_adomd.ps1`

---

## Licencia

MIT