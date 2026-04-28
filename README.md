# powerbi-mcp-server

Repositorio con servidor MCP para inspeccionar modelos de Power BI y herramientas auxiliares.

## Instalación de ADOMD (reproducible vía NuGet)

Este proyecto usa `pyadomd` para conectarse a modelos locales XMLA. ADOMD.NET (la DLL `AdomdClient.dll`) ahora se distribuye vía NuGet; para evitar instalar MSIs a mano se incluye un script que descarga el paquete NuGet y extrae la DLL.

Para extraer la DLL y copiarla a `vendor/adomd/` ejecuta (PowerShell):

```powershell
# Desde la raíz del repo (puedes ejecutar como Administrador si deseas copiar al venv)
.\n+\.\scripts\install_adomd.ps1
```

Opcionalmente puedes pasar `-CopyToVenv` para que intente copiar la DLL a `\.venv\Lib\site-packages`.

## Uso rápido

1. Activa tu entorno virtual

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\.venv\Scripts\Activate.ps1")
```

### Verificar conexión Power BI (rápido)

Si necesitas comprobar de forma reproducible que las DLLs ADOMD.NET y `pyadomd` funcionan en este equipo, ejecuta:

```powershell
python -m pip install -r requirements.txt
python .\scripts\verify_powerbi_connection.py
```

El script buscará la instancia local de Power BI Desktop (AnalysisServicesWorkspaces), cargará las DLL en `vendor/adomd` y ejecutará una consulta DAX mínima. Devuelve JSON con detalles y errores.

2. Instala dependencias Python

```powershell
pip install -r requirements.txt
```

3. Extrae ADOMD desde NuGet (si no lo hiciste ya)

```powershell
\.\scripts\install_adomd.ps1 -CopyToVenv
```

4. Inicia el servidor MCP

```powershell
python -m src.server
```

## Alternativa (REST)

Si no quieres depender de ADOMD.NET, puedo añadir un endpoint REST/JSON (FastAPI) para prototipado y permitir que Power BI consuma datos vía `Obtener datos > Web`.

## Ejemplos y vendor

- Los scripts de ejemplo se movieron a `examples/`.
- Las DLLs `AdomdClient.dll` y `Tabular.dll` no se versionan en este repositorio. Colócalas en `vendor/adomd/` y `vendor/tom/` si deseas usarlas localmente.

