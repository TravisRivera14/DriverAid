# sim_backend.py — Backend de simulación (macOS/Linux o modo demo)
from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime
import csv

@dataclass
class Driver:
    id: int
    device: str
    provider: str
    version_installed: str
    version_latest: str
    hardware_id: str
    status: str = field(default="Desconocido")
    manual_link: str = field(default="")

    def refresh_status(self):
        self.status = "Actualizado" if self.version_installed == self.version_latest else "Desactualizado"
        if not self.manual_link:
            q = self.hardware_id.replace(" ", "%20")
            self.manual_link = f"https://www.catalog.update.microsoft.com/Search.aspx?q={q}"

def _sample_data() -> List["Driver"]:
    raw = [
        (1, "Adaptador de Red Intel I219-V", "Intel", "12.19.1.37", "12.19.1.39", "PCI\\VEN_8086&DEV_15BE"),
        (2, "Audio High Definition", "Realtek", "6.0.1.8703", "6.0.1.9107", "HDAUDIO\\FUNC_01&VEN_10EC&DEV_0295"),
        (3, "Controlador SATA AHCI", "Microsoft", "10.0.19041.1", "10.0.19041.1", "PCI\\VEN_8086&DEV_A102"),
        (4, "Gráficos UHD", "Intel", "30.0.101.1191", "31.0.101.5534", "PCI\\VEN_8086&DEV_9A60"),
        (5, "Impresora USB Genérica", "USB-IF", "1.0.0", "1.0.2", "USB\\VID_1234&PID_5678"),
    ]
    items = [Driver(*r) for r in raw]
    for d in items:
        d.refresh_status()
    return items

class SimBackend:
    def __init__(self):
        self.drivers: List[Driver] = _sample_data()

    # 1) Escaneo
    def scan(self) -> List[Driver]:
        for d in self.drivers:
            d.refresh_status()
        return self.drivers

    # 2) Filtrar desactualizados
    def outdated(self) -> List[Driver]:
        return [d for d in self.drivers if d.status == "Desactualizado"]

    # 3) Actualizar todos (simulado)
    def update_all(self) -> Tuple[int, int]:
        updated = 0; skipped = 0
        for d in self.drivers:
            d.refresh_status()
            if d.status == "Desactualizado":
                d.version_installed = d.version_latest
                d.refresh_status()
                updated += 1
            else:
                skipped += 1
        return updated, skipped

    # 4) Actualizar uno por ID (simulado)
    def update_one(self, driver_id: int) -> bool:
        for d in self.drivers:
            if d.id == driver_id:
                d.version_installed = d.version_latest
                d.refresh_status()
                return True
        return False

    # 5) Generar reporte (HTML y CSV)
    def export_report(self, folder: str) -> Tuple[str, str]:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        html_path = f"{folder}/DriverAid-Report-{ts}.html"
        csv_path  = f"{folder}/DriverAid-Report-{ts}.csv"

        rows = []
        for d in self.drivers:
            rows.append(
                f"<tr><td>{d.id}</td><td>{d.device}</td><td>{d.provider}</td>"
                f"<td>{d.version_installed}</td><td>{d.version_latest}</td>"
                f"<td>{d.status}</td><td><a href='{d.manual_link}' target='_blank'>Catálogo</a></td></tr>"
            )
        html = f"""<html><head><meta charset="utf-8"><title>DriverAid Report</title>
<style>body{{font-family:Segoe UI, Arial}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px}} th{{background:#f2f2f2}}</style></head>
<body><h1>DriverAid - Reporte (simulado)</h1>
<p>Fecha: {datetime.now()}</p>
<table><thead><tr>
<th>ID</th><th>Dispositivo</th><th>Proveedor</th><th>Instalada</th><th>Última</th><th>Estado</th><th>Link</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID","Dispositivo","Proveedor","VersionInstalada","VersionLatest","Estado","Link"])
            for d in self.drivers:
                writer.writerow([d.id,d.device,d.provider,d.version_installed,d.version_latest,d.status,d.manual_link])

        return html_path, csv_path

    # 6) Obtener links
    def manual_links(self):
        return [(d.id, d.device, d.manual_link) for d in self.drivers]
