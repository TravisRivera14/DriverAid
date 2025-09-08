; DriverAid.iss — Instalador de DriverAid by Travis (actualizado a DriverAid.exe)

[Setup]
AppName=DriverAid by Travis
AppVersion=1.0.0
AppPublisher=Travis Rivera
AppPublisherURL=https://example.com
DefaultDirName={pf}\DriverAid
DefaultGroupName=DriverAid
OutputBaseFilename=DriverAid-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
SetupLogging=yes
SetupIconFile=assets\DriverAid.ico

[Files]
; ⬇️ IMPORTANTE: ahora tomamos DriverAid.exe (no main.exe)
Source: "dist\DriverAid.exe"; DestDir: "{app}"; Flags: ignoreversion
; Carpetas opcionales (no fallan si están vacías)
Source: "drivers\*"; DestDir: "{app}\drivers"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "reports\*"; DestDir: "{app}\reports"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
; Módulo opcional a futuro
; Source: "modules\PSWindowsUpdate\*"; DestDir: "{app}\modules\PSWindowsUpdate"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\DriverAid"; Filename: "{app}\DriverAid.exe"; IconFilename: "{app}\DriverAid.ico"; IconIndex: 0
Name: "{commondesktop}\DriverAid"; Filename: "{app}\DriverAid.exe"; IconFilename: "{app}\DriverAid.ico"; IconIndex: 0; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\DriverAid.exe"; Description: "Iniciar DriverAid"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\reports"
