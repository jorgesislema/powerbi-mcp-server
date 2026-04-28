# Ejecutar en PowerShell (Run as Administrator)
$ErrorActionPreference = 'Stop'

# 1) Abrir página oficial para descargar ADOMD.NET x64 (elige la versión recomendada)
Start-Process "https://learn.microsoft.com/en-us/analysis-services/adomd/adomdnet?view=asallproducts"

Write-Host "Abriendo la documentación de ADOMD.NET en el navegador. Descarga la versión x64 adecuada y guarda el MSI en una carpeta (ej: C:\Temp). Presiona Enter cuando el MSI esté descargado."
Read-Host

# 2) Pide la ruta local al MSI descargado
$msiPath = Read-Host "Ruta completa al MSI de ADOMD.NET (ej: C:\Temp\MSOLAP.msi)"

if (-not (Test-Path $msiPath)) {
    Write-Error "No se encontró el archivo: $msiPath"
    exit 1
}

# 3) Ejecutar instalador (pedirá elevación si no estás en Administrador)
Write-Host "Instalando ADOMD.NET desde $msiPath ..."
Start-Process msiexec.exe -ArgumentList "/i", "`"$msiPath`"", "/qn", "/norestart" -Wait -NoNewWindow
Write-Host "Instalación completada (si el instalador no soporta /qn puede que haya mostrado UI)."

# 4) Localizar carpeta donde quedó AdomdClient.dll (intenta rutas comunes)
$possiblePaths = @(
    "C:\Program Files\Microsoft Analysis Services\AS OLEDB\",
    "C:\Program Files\Microsoft Analysis Services ADOMD.NET\",
    "C:\Program Files\Microsoft ADOMD.NET\",
    "C:\Program Files\Microsoft\ADOMD.NET\",
    "C:\Program Files\Microsoft SQL Server\"
)

$found = $null
foreach ($p in $possiblePaths) {
    if (Test-Path $p) {
        $dll = Get-ChildItem -Path $p -Recurse -Filter "AdomdClient.dll" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($dll) { $found = $dll.FullName; break }
    }
}

if ($found) {
    Write-Host "AdomdClient.dll encontrado en: $found"
    $dllFolder = Split-Path $found -Parent
    Write-Host "Añadiendo temporalmente a PATH para la sesión actual..."
    $env:PATH = $dllFolder + ";" + $env:PATH
} else {
    Write-Warning "No se encontró AdomdClient.dll automáticamente. Si el instalador lo colocó en otra ruta, añade esa carpeta al PATH del sistema."
}

# 5) Instalar pyadomd en el venv del repo
$repo = Resolve-Path ".\"
# Detectar venv: .venv en repo o ../.venv
$venvCandidates = @(".\.venv\Scripts\python.exe", ".\venv\Scripts\python.exe", "..\.venv\Scripts\python.exe")
$py = $null
foreach ($v in $venvCandidates) {
    if (Test-Path $v) { $py = (Resolve-Path $v).Path; break }
}
if (-not $py) {
    # fallback al python del PATH
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) { $py = $pyCmd.Source }
}

if (-not $py) {
    Write-Error "No se encontró un intérprete Python. Activa tu venv o instala Python."
    exit 1
}

Write-Host "Usando Python: $py"
& $py -m pip install --upgrade pip
& $py -m pip install pyadomd

Write-Host "Instalación de pyadomd finalizada. Verifica con:"
Write-Host "`n$py -c \"import pyadomd; print('pyadomd OK')\"`n"
Write-Host "Y prueba el cliente:"
Write-Host "`n$py -c \"from src.powerbi_client import PowerBIClient; c=PowerBIClient(); print(c.discover_local_instances()); print(c.refresh_connection())\"`n"

Write-Host "Si todo está OK, reinicia VS Code/terminal y arranca el servidor MCP:" 
Write-Host "`npython -m src.server`"
<#
Script: scripts/install_adomd.ps1
Descripción: Descarga el paquete NuGet 'Microsoft.AnalysisServices.AdomdClient', extrae
la DLL `AdomdClient.dll` y la copia a `vendor/adomd/` (y opcionalmente al venv).

Uso:
  Ejecutar PowerShell como Administrador en la raíz del repo:
    .\scripts\install_adomd.ps1

Notas:
 - Requiere `nuget.exe` (se descargará automáticamente si hace falta).
 - Asegúrate que la arquitectura (x64/x86) de Python coincide con la DLL.
#>

Param(
    [string]$OutputDir = "packages",
    [string]$VendorDir = "vendor\adomd",
    [switch]$CopyToVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "== install_adomd.ps1: inicio =="

# Crear carpetas
New-Item -Path . -Name $OutputDir -ItemType Directory -Force | Out-Null
New-Item -Path . -Name $VendorDir -ItemType Directory -Force | Out-Null

$toolsDir = Join-Path -Path '.' -ChildPath 'tools'
if (-not (Test-Path $toolsDir)) { New-Item -Path $toolsDir -ItemType Directory | Out-Null }
$nugetExe = Join-Path $toolsDir 'nuget.exe'

if (-not (Test-Path $nugetExe)) {
    Write-Host "Descargando nuget.exe..."
    Invoke-WebRequest -Uri 'https://dist.nuget.org/win-x86-commandline/latest/nuget.exe' -OutFile $nugetExe
}

Write-Host "Descargando paquete NuGet 'Microsoft.AnalysisServices.AdomdClient'..."
& $nugetExe install Microsoft.AnalysisServices.AdomdClient -OutputDirectory $OutputDir -ExcludeVersion | Out-Null

Write-Host "Buscando la DLL principal y dependencias en $OutputDir ..."
# Priorizar la DLL exacta Microsoft.AnalysisServices.AdomdClient.dll en carpetas lib/net* (no en subcarpetas de idiomas)
$preferred = Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ieq 'Microsoft.AnalysisServices.AdomdClient.dll' -and ($_.FullName -match '\\lib\\net') } |
    Sort-Object FullName | Select-Object -First 1

if (-not $preferred) {
    # fallback: buscar cualquier DLL con 'AdomdClient' o 'AnalysisServices' (ignorar archivos '.resources.dll')
    $preferred = Get-ChildItem -Path $OutputDir -Recurse -Include '*AdomdClient*.dll','*AnalysisServices*.dll' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '*.resources.dll' } | Select-Object -First 1
}

if (-not $preferred) {
    Write-Error "No se encontró ninguna DLL relevante (ej. Microsoft.AnalysisServices.AdomdClient.dll) en el paquete NuGet. Revisa $OutputDir para versiones disponibles."
    exit 1
}

# Copiar la DLL principal
$mainDll = $preferred
$destMain = Join-Path -Path $VendorDir -ChildPath $mainDll.Name
Copy-Item -Path $mainDll.FullName -Destination $destMain -Force
Write-Host "Copiado: $($mainDll.FullName) -> $destMain"

# Intentar localizar dependencias comunes y copiarlas también (Runtime.Core, Runtime.Windows)
$deps = @('Microsoft.AnalysisServices.Runtime.Core.dll','Microsoft.AnalysisServices.Runtime.Windows.dll')
# Guardar lista de archivos copiados para poder replicarlos al venv
$copiedFiles = @()
$copiedFiles += $destMain
foreach ($dep in $deps) {
    $f = Get-ChildItem -Path $OutputDir -Recurse -Filter $dep -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($f) {
        $destDep = Join-Path -Path $VendorDir -ChildPath $f.Name
        Copy-Item -Path $f.FullName -Destination $destDep -Force
        Write-Host "Copiado dependencia: $($f.FullName) -> $destDep"
        $copiedFiles += $destDep
    }
}

if ($CopyToVenv) {
    Write-Host "Intentando copiar a la carpeta site-packages del venv..."
    $venvCandidates = @('.\.venv\Lib\site-packages', '.\venv\Lib\site-packages', '..\.venv\Lib\site-packages')
    $found = $null
    foreach ($c in $venvCandidates) {
        if (Test-Path $c) { $found = (Resolve-Path $c).Path; break }
    }
    if ($found) {
        foreach ($p in $copiedFiles) {
            $target = Join-Path $found (Split-Path $p -Leaf)
            Copy-Item -Path $p -Destination $target -Force
            Write-Host "Copiado al venv: $p -> $target"
        }
        Write-Host "DLL(s) copiadas a venv site-packages: $found"
    } else {
        Write-Warning "No se encontró venv site-packages automáticamente. Activa tu venv y copia los archivos en $VendorDir manualmente si lo deseas."
    }
}

Write-Host "== install_adomd.ps1: terminado =="
