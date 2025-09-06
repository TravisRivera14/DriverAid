# win_backend.py — Backend REAL para Windows (inventario, updates online y OFFLINE con pnputil)
from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime
import csv
import json
import os
import subprocess

try:
    import wmi  # pip install wmi
except ImportError:
    wmi = None

@dataclass
class Driver:
    id: int
    device: str
    provider: str
    version_installed: str
    version_latest: str
    hardware_id: str
    status: str = field(default="Desconocido")  # "Actualizado" | "Desactualizado" | "Desconocido"
    manual_link: str = field(default="")        # Microsoft Update Catalog por HWID

    def refresh_status(self):
        if self.version_latest and self.version_installed:
            self.status = "Actualizado" if self.version_installed == self.version_latest else "Desactualizado"
        else:
            if self.status not in ("Actualizado", "Desactualizado"):
                self.status = "Desconocido"
        if not self.manual_link and self.hardware_id:
            first = self.hardware_id.split(",")[0].strip()
            q = first.replace(" ", "%20")
            self.manual_link = f"https://www.catalog.update.microsoft.com/Search.aspx?q={q}"

class WinBackend:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("WinBackend solo puede ejecutarse en Windows.")
        if wmi is None:
            raise RuntimeError("Falta el módulo 'wmi'. Instala con: pip install wmi")
        self._drivers: List[Driver] = []
        self._updates: List[dict] = []  # cache de updates (PSWindowsUpdate)

    # -------------------- Utilidades PowerShell --------------------
    def _ps(self, script: str) -> Tuple[int, str, str]:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]
        cp = subprocess.run(cmd, capture_output=True, text=True)
        return cp.returncode, cp.stdout, cp.stderr

    def _ensure_microsoft_update(self):
        self._ps("Try { Add-WUServiceManager -MicrosoftUpdate -ErrorAction SilentlyContinue | Out-Null } Catch {}")

    def _get_driver_updates(self) -> List[dict]:
        self._ensure_microsoft_update()
        ps = r"""
$ErrorActionPreference='SilentlyContinue'
Import-Module PSWindowsUpdate -ErrorAction SilentlyContinue
$u = Get-WindowsUpdate -MicrosoftUpdate -Category 'Drivers' -IgnoreReboot -ErrorAction SilentlyContinue
if ($u) {
  $u | Select-Object Title,KB,Size,Categories,IsDownloaded,IsInstalled,AutoSelectOnWebSites |
  ConvertTo-Json -Depth 4
} else {
  "[]"
}
"""
        rc, out, err = self._ps(ps)
        try:
            updates = json.loads(out) if out.strip() else []
        except json.JSONDecodeError:
            updates = []
        return updates if isinstance(updates, list) else []

    # -------------------- Inventario --------------------
    def scan(self) -> List[Driver]:
        c = wmi.WMI()
        items: List[Driver] = []
        idx = 1
        for d in c.Win32_PnPSignedDriver():
            dev = getattr(d, "DeviceName", None) or getattr(d, "FriendlyName", "") or ""
            inst_ver = getattr(d, "DriverVersion", "") or ""
            prov = getattr(d, "DriverProviderName", "") or ""
            hwid = ""
            try:
                hw = getattr(d, "HardwareID", None)
                if hw:
                    hwid = ", ".join(hw)
            except Exception:
                pass

            items.append(Driver(
                id=idx,
                device=str(dev),
                provider=str(prov),
                version_installed=str(inst_ver),
                version_latest="",
                hardware_id=hwid
            ))
            idx += 1

        self._drivers = items

        self._updates = self._get_driver_updates()
        titles = [u.get("Title", "") for u in self._updates]

        for drv in self._drivers:
            drv.refresh_status()
            low_dev = drv.device.lower() if drv.device else ""
            low_prov = drv.provider.lower() if drv.provider else ""
            if any((low_dev and low_dev in t.lower()) or (low_prov and low_prov in t.lower()) for t in titles):
                drv.status = "Desactualizado"
            else:
                if not self._updates:
                    drv.status = "Actualizado"
            drv.refresh_status()

        return self._drivers

    def outdated(self) -> List[Driver]:
        if not self._drivers:
            self.scan()
        return [d for d in self._drivers if d.status == "Desactualizado"]

    # -------------------- Actualización (Online) --------------------
    def update_all(self) -> Tuple[int, int]:
        self._ensure_microsoft_update()
        ps = r"""
$ErrorActionPreference='SilentlyContinue'
Import-Module PSWindowsUpdate -ErrorAction SilentlyContinue
Install-WindowsUpdate -MicrosoftUpdate -Category 'Drivers' -AcceptAll -IgnoreReboot -ErrorAction SilentlyContinue | Out-Null
"""
        _rc, _out, _err = self._ps(ps)
        before = len(self.outdated())
        self.scan()
        after = len(self.outdated())
        updated = max(before - after, 0)
        skipped = len(self._drivers) - updated
        return updated, skipped

    def update_one(self, driver_id: int) -> bool:
        if not self._drivers:
            self.scan()
        target = next((d for d in self._drivers if d.id == driver_id), None)
        if not target:
            return False

        if not self._updates:
            self._updates = self._get_driver_updates()

        title_match = None
        for u in self._updates:
            title = u.get("Title", "")
            if target.device and target.device.lower() in title.lower():
                title_match = title; break
            if target.provider and target.provider.lower() in title.lower():
                title_match = title; break

        if not title_match:
            return False

        safe = title_match.replace('"', '`"')
        ps = fr"""
$ErrorActionPreference='SilentlyContinue'
Import-Module PSWindowsUpdate -ErrorAction SilentlyContinue
$u = Get-WindowsUpdate -MicrosoftUpdate -Category 'Drivers' -IgnoreReboot | Where-Object {{ $_.Title -like "*{safe}*" }}
if ($u) {{
  Install-WindowsUpdate -Updates $u -AcceptAll -IgnoreReboot -ErrorAction SilentlyContinue | Out-Null
}}
"""
        _rc, _out, _err = self._ps(ps)
        self.scan()
        return True

    # -------------------- Instalación OFFLINE (pnputil + .INF) --------------------
    def install_offline(self, folder: str) -> Tuple[int, str]:
        folder_abs = os.path.abspath(folder)
        if not os.path.isdir(folder_abs):
            return -1, f"La carpeta no existe: {folder_abs}"
        win_path = folder_abs.replace("/", "\\")
        pattern = rf"{win_path}\*.inf"
        cmd = ["pnputil.exe", "/add-driver", pattern, "/subdirs", "/install"]
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True)
            return cp.returncode, (cp.stdout or "") + (cp.stderr or "")
        except Exception as e:
            return -1, f"Error ejecutando pnputil: {e}"

    # -------------------- Reportes / Links --------------------
    def export_report(self, folder: str) -> Tuple[str, str]:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        html_path = os.path.join(folder, f"DriverAid-Report-{ts}.html")
        csv_path = os.path.join(folder, f"DriverAid-Report-{ts}.csv")

        data = self._drivers or self.scan()

        rows = []
        for d in data:
            rows.append(
                f"<tr><td>{d.id}</td><td>{d.device}</td><td>{d.provider}</td>"
                f"<td>{d.version_installed}</td><td>{d.version_latest}</td>"
                f"<td>{d.status}</td><td><a href='{d.manual_link}' target='_blank'>Catálogo</a></td></tr>"
            )
        html = f"""<html><head><meta charset="utf-8"><title>DriverAid Report</title>
<style>body{{font-family:Segoe UI, Arial}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px}} th{{background:#f2f2f2}}</style></head>
<body><h1>DriverAid - Reporte (Windows Real)</h1>
<p>Fecha: {datetime.now()}</p>
<table><thead><tr>
<th>ID</th><th>Dispositivo</th><th>Proveedor</th><th>Instalada</th><th>Última</th><th>Estado</th><th>Link</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Dispositivo", "Proveedor", "VersionInstalada", "VersionLatest", "Estado", "Link"])
            for d in data:
                writer.writerow([d.id, d.device, d.provider, d.version_installed, d.version_latest, d.status, d.manual_link])

        return html_path, csv_path

    def manual_links(self):
        if not self._drivers:
            self.scan()
        return [(d.id, d.device, d.manual_link) for d in self._drivers]
