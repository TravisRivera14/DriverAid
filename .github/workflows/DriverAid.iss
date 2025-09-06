; DriverAid.iss — Instalador de DriverAid by Travis

[Setup]
AppName=DriverAid by Travis
AppVersion=1.0.0
AppPublisher=Travis Rivera
DefaultDirName={pf}\DriverAid
DefaultGroupName=DriverAid
OutputBaseFilename=DriverAid-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "drivers\*"; DestDir: "{app}\drivers"; Flags: recursesubdirs createallsubdirs
Source: "reports\*"; DestDir: "{app}\reports"; Flags: recursesubdirs createallsubdirs
; Si alguna vez vendorizas PSWindowsUpdate:
; Source: "modules\PSWindowsUpdate\*"; DestDir: "{app}\modules\PSWindowsUpdate"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DriverAid"; Filename: "{app}\main.exe"
Name: "{commondesktop}\DriverAid"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\main.exe"; Description: "Iniciar DriverAid"; Flags: nowait postinstall skipifsilent
