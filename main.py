# main.py - DriverAid (Simulador / Windows Real) con preflight automático + opción 7 OFFLINE
import os
import sys
import platform
import logging
from datetime import datetime
import subprocess

# ================== Preflight Windows ==================
def _is_windows():
    return platform.system() == "Windows"

def ensure_admin_windows():
    """Relanza el proceso con permisos de admin si no los tiene (dispara UAC)."""
    if not _is_windows():
        return
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            params = " ".join([f'"{p}"' if " " in p else p for p in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit(0)
    except Exception:
        # Si falla la detección, seguimos normal (algunas UIs especiales)
        pass

def ensure_python_dep(pkg, import_name=None):
    """Instala un paquete pip si no está disponible."""
    mod = import_name or pkg
    try:
        __import__(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def _prefer_local_pswindowsupdate():
    """
    Si existe un módulo local en .\modules\PSWindowsUpdate, lo antepone al PSModulePath
    (útil en entornos corporativos sin PSGallery).
    """
    if not _is_windows():
        return
    local = os.path.join(os.path.dirname(__file__), "modules", "PSWindowsUpdate")
    if os.path.isdir(local):
        # Prepend al PSModulePath
        cur = os.environ.get("PSModulePath", "")
        if local not in cur:
            os.environ["PSModulePath"] = f"{local};{cur}" if cur else local

def ensure_pswindowsupdate():
    """Instala y activa PSWindowsUpdate + Microsoft Update (si no está)."""
    _prefer_local_pswindowsupdate()
    ps = r"""
$ErrorActionPreference='SilentlyContinue'
# Instalar NuGet provider si falta
if (-not (Get-PackageProvider -Name NuGet -ListAvailable)) {
  Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force | Out-Null
}
# Confiar en PSGallery
try { Set-PSRepository -Name PSGallery -InstallationPolicy Trusted } catch {}
# Instalar módulo si falta
if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) {
  try { Install-Module PSWindowsUpdate -Force } catch {}
}
Import-Module PSWindowsUpdate -ErrorAction SilentlyContinue
# Agregar Microsoft Update
try { Add-WUServiceManager -MicrosoftUpdate -Confirm:$false | Out-Null } catch {}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=False, text=True, capture_output=True
    )

# Ejecuta preflight si estamos en Windows
ensure_admin_windows()
if _is_windows():
    ensure_python_dep("wmi")
    ensure_pswindowsupdate()

# ================== Selección de backend ==================
if _is_windows():
    from win_backend import WinBackend as Backend
else:
    from sim_backend import SimBackend as Backend

# ================== Configuración ==================
BASE_DIR = os.path.dirname(__file__)
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DRIVERS_DIR = os.path.join(BASE_DIR, "drivers")
LOG_PATH = os.path.join(REPORTS_DIR, "activity.log")

class S:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"; GRAY = "\033[90m"

def banner():
    art = r"""
   ____  _           _            _      _     _ 
  |  _ \(_)_ __   __| |_ __ _   _| |__  (_)___| |
  | | | | | '_ \ / _` | '__| | | | '_ \ | / __| |
  | |_| | | | | | (_| | |  | |_| | |_) || \__ \_|
  |____/|_|_| |_|\__,_|_|   \__,_|_.__(_)_|___(_)
        DriverAid (Simulador / Windows)
    """
    print(S.CYAN + art + S.RESET)

def ensure_reports():
    os.makedirs(REPORTS_DIR, exist_ok=True)

def setup_logging():
    ensure_reports()
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logging.info("=== Inicio de sesión DriverAid ===")

def clear():
    os.system("cls" if _is_windows() else "clear")

def pause():
    try:
        input(S.GRAY + "\nPresiona Enter para continuar..." + S.RESET)
    except EOFError:
        pass

def print_header(title: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(S.BOLD + f"\n{title}" + S.RESET + S.GRAY + f"  ({now})" + S.RESET)

def color_status(status: str) -> str:
    s = (status or "").lower()
    if s.startswith("act"):
        return S.GREEN + status + S.RESET
    elif s.startswith(("des","out")):
        return S.YELLOW + status + S.RESET
    return S.RED + (status or "Desconocido") + S.RESET

def print_table(items):
    headers = ["ID", "Dispositivo", "Proveedor", "Instalada", "Última", "Estado"]
    rows = [[str(d.id), d.device, d.provider, d.version_installed, d.version_latest, d.status] for d in items]
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print("\n" + S.BOLD + line + S.RESET)
    print("-" * (len(line)))
    for r in rows:
        r[5] = color_status(r[5])
        print(" | ".join(r[i].ljust(widths[i]) for i in range(len(headers))))

# ================== Main ==================
def main():
    ensure_reports()
    setup_logging()

    backend = Backend()
    so = platform.system()
    is_windows = (so == "Windows")
    clear()
    banner()
    print(S.DIM + f"Sistema operativo detectado: {so}" + S.RESET)

    while True:
        print("\n" + S.BOLD + "Menú principal" + S.RESET)
        print("1) Escanear e inventariar drivers")
        print("2) Ver solo desactualizados")
        print("3) Actualizar TODOS")
        print("4) Actualizar MANUAL (elige por ID)")
        print("5) Generar reporte (HTML y CSV)")
        print("6) Mostrar links de descarga manual")
        if is_windows:
            print("7) Instalar drivers desde carpeta ./drivers (OFFLINE, requiere Admin)")
        print("0) Salir")
        choice = input("\nElige una opción: ").strip()

        if choice == "1":
            items = backend.scan()
            print_header("Inventario de drivers")
            print_table(items); pause()

        elif choice == "2":
            items = backend.outdated()
            print_header("Drivers desactualizados")
            if items: print_table(items)
            else: print(S.GREEN + "\nTodo actualizado 🎉" + S.RESET)
            pause()

        elif choice == "3":
            updated, skipped = backend.update_all()
            print(S.CYAN + f"\nActualizados: {updated} | Omitidos: {skipped}" + S.RESET); pause()

        elif choice == "4":
            idx = input("Ingresa el ID del driver a actualizar: ").strip()
            if not idx.isdigit():
                print(S.RED + "ID inválido ❌" + S.RESET); pause(); continue
            ok = backend.update_one(int(idx))
            print(S.GREEN + "Actualizado ✅" + S.RESET if ok else S.RED + "ID no encontrado ❌" + S.RESET); pause()

        elif choice == "5":
            html, csv = backend.export_report(REPORTS_DIR)
            print(S.GREEN + "\nReportes creados:" + S.RESET)
            print("•", html); print("•", csv); pause()

        elif choice == "6":
            print_header("Links de descarga manual")
            for id_, name, link in backend.manual_links():
                print(f"{str(id_).rjust(2)} | {name} -> {link}")
            pause()

        elif choice == "7" and is_windows:
            print_header("Instalación OFFLINE desde .\\drivers")
            print(S.DIM + "Coloca paquetes con .INF dentro de ./drivers (recursivo)." + S.RESET)
            default = DRIVERS_DIR
            path = input(f"Ruta de carpeta (Enter para usar por defecto: {default}): ").strip() or default
            try:
                rc, out = backend.install_offline(path)  # type: ignore[attr-defined]
                print("\nCódigo de retorno:", rc)
                print(out if out else "(sin salida)")
                if rc == 0:
                    print(S.GREEN + "\nInstalación offline finalizada (puede requerir reinicio)." + S.RESET)
                elif rc == -1:
                    print(S.RED + "\nError: revise la ruta o permisos (ejecutar como Administrador)." + S.RESET)
                else:
                    print(S.YELLOW + "\npnputil devolvió un código distinto de 0. Revise el detalle arriba." + S.RESET)
            except AttributeError:
                print(S.RED + "El backend actual no soporta instalación offline." + S.RESET)
            pause()

        elif choice == "0":
            print(S.DIM + "\nGracias por usar DriverAid. ¡Hasta pronto!" + S.RESET); break
        else:
            print(S.RED + "Opción inválida ❌" + S.RESET); pause()

        clear(); banner()
        print(S.DIM + f"Sistema operativo detectado: {so}" + S.RESET)

if __name__ == "__main__":
    main()
