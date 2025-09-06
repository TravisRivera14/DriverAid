Write-Host "Lanzador PowerShell DriverAid"
if (Test-Path ".\dist\main.exe") { & ".\dist\main.exe" }
elseif (Test-Path ".\main.exe") { & ".\main.exe" }
else { Write-Host "No se encontró main.exe" }
