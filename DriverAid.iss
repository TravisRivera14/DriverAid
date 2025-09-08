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
DisableDirPage=no
DisableProgramGroupPage=yes
WizardStyle=modern
SetupLogging=yes

[Files]
; Binario principal
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion

; Contenido opcional: si la carpeta está vacía, NO falla gracias a skipifsourcedoesntexist
Source: "drivers\*"; DestDir: "{app}\drivers"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "reports\*"; DestDir: "{app}\reports"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
; Si en el futuro vendorizas PSWindowsUpdate:
; Source: "modules\PSWindowsUpdate\*"; DestDir: "{app}\modules\PSWindowsUpdate"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\DriverAid"; Filename: "{app}\main.exe"
Name: "{commondesktop}\DriverAid"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
; Lanza la app al finalizar la instalación (sin bloquear el asistente)
Filename: "{app}\main.exe"; Description: "Iniciar DriverAid"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpia informes generados por el usuario en desinstalación
Type: filesandordirs; Name: "{app}\reports"
