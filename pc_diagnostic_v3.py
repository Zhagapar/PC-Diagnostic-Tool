
import os
import platform
import socket
import shutil
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime


# ---------- Цвета интерфейса ----------

BG = "#111827"
PANEL = "#1F2937"
PANEL_LIGHT = "#273449"
TEXT = "#F3F4F6"
MUTED = "#9CA3AF"
ACCENT = "#38BDF8"
GREEN = "#34D399"
YELLOW = "#FBBF24"
RED = "#F87171"


def get_memory_info():
    """Возвращает общий объём и свободную физическую память."""
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    try:
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

        if ctypes.windll.kernel32.GlobalMemoryStatusEx(
            ctypes.byref(status)
        ):
            total = status.ullTotalPhys
            available = status.ullAvailPhys
            used_percent = status.dwMemoryLoad

            return {
                "total": total,
                "available": available,
                "used_percent": used_percent,
            }
    except (AttributeError, OSError):
        pass

    return None


def get_system_info():
    memory = get_memory_info()

    return {
        "Имя компьютера": socket.gethostname(),
        "Операционная система": platform.platform(),
        "Процессор": platform.processor() or "Не определён",
        "Архитектура": platform.machine(),
        "Логические потоки CPU": os.cpu_count() or 0,
        "RAM": memory,
    }


def get_disk_info():
    disks = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        path = f"{letter}:\\"

        if not os.path.exists(path):
            continue

        try:
            usage = shutil.disk_usage(path)
            used = usage.total - usage.free
            percent = used / usage.total * 100 if usage.total else 0

            disks.append({
                "name": f"{letter}:",
                "path": path,
                "total": usage.total,
                "used": used,
                "free": usage.free,
                "percent": percent,
            })
        except OSError:
            continue

    return disks


def gb(value):
    return f"{value / (1024 ** 3):.2f} ГБ"


class DiagnosticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Diagnostic Tool v3")
        self.root.geometry("900x720")
        self.root.minsize(700, 580)
        self.root.configure(bg=BG)

        self.system_info = {}
        self.disks = []

        self.create_styles()
        self.create_interface()
        self.refresh()
        self.root.after(5000, self.auto_refresh)

    def create_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=PANEL_LIGHT,
            background=GREEN,
            bordercolor=PANEL_LIGHT,
            lightcolor=GREEN,
            darkcolor=GREEN,
        )

    def create_interface(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=22, pady=(20, 12))

        tk.Label(
            header,
            text="PC DIAGNOSTIC TOOL",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Мониторинг и диагностика компьютера",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        self.cards = tk.Frame(self.root, bg=BG)
        self.cards.pack(fill="x", padx=16, pady=6)

        self.cpu_card = self.create_card(
            self.cards, "ПРОЦЕССОР", "Определение..."
        )
        self.cpu_card.pack(
            side="left", fill="both", expand=True, padx=6
        )

        self.ram_card = self.create_card(
            self.cards, "ОПЕРАТИВНАЯ ПАМЯТЬ", "Определение..."
        )
        self.ram_card.pack(
            side="left", fill="both", expand=True, padx=6
        )

        self.os_card = self.create_card(
            self.cards, "СИСТЕМА", "Загрузка..."
        )
        self.os_card.pack(
            side="left", fill="both", expand=True, padx=6
        )

        disk_header = tk.Frame(self.root, bg=BG)
        disk_header.pack(fill="x", padx=22, pady=(18, 8))

        tk.Label(
            disk_header,
            text="НАКОПИТЕЛИ",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        self.disk_count = tk.Label(
            disk_header,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        )
        self.disk_count.pack(side="right")

        self.disk_frame = tk.Frame(self.root, bg=BG)
        self.disk_frame.pack(
            fill="both", expand=True, padx=22, pady=4
        )

        controls = tk.Frame(self.root, bg=BG)
        controls.pack(fill="x", padx=22, pady=(12, 4))

        tk.Button(
            controls,
            text="⟳  Обновить",
            command=self.refresh,
            bg=ACCENT,
            fg="#0B1220",
            activebackground="#7DD3FC",
            relief="flat",
            padx=16,
            pady=9,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            controls,
            text="Сохранить отчёт",
            command=self.save_report,
            bg=PANEL_LIGHT,
            fg=TEXT,
            activebackground="#374151",
            activeforeground=TEXT,
            relief="flat",
            padx=16,
            pady=9,
            font=("Segoe UI", 10),
            cursor="hand2",
        ).pack(side="left")

        self.status = tk.Label(
            self.root,
            text="Ожидание данных...",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.status.pack(fill="x", padx=22, pady=(8, 14))

    def create_card(self, parent, title, initial_value):
        card = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground="#374151",
            highlightthickness=1,
            padx=14,
            pady=14,
        )

        tk.Label(
            card,
            text=title,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
            wraplength=180,
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=initial_value,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
            wraplength=210,
            justify="left",
        )
        value_label.pack(anchor="w", pady=(12, 5))

        detail_label = tk.Label(
            card,
            text="",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=210,
            justify="left",
        )
        detail_label.pack(anchor="w")

        card.value_label = value_label
        card.detail_label = detail_label

        return card

    def refresh(self):
        try:
            self.system_info = get_system_info()
            self.disks = get_disk_info()

            cpu = self.system_info["Процессор"]
            threads = self.system_info["Логические потоки CPU"]

            self.cpu_card.value_label.config(
                text=f"{threads} поток(а)"
            )
            self.cpu_card.detail_label.config(
                text=cpu
            )

            memory = self.system_info["RAM"]

            if memory:
                used = memory["total"] - memory["available"]

                self.ram_card.value_label.config(
                    text=f"{memory['used_percent']}% занято"
                )
                self.ram_card.detail_label.config(
                    text=(
                        f"{gb(used)} из {gb(memory['total'])}\n"
                        f"Свободно: {gb(memory['available'])}"
                    )
                )
            else:
                self.ram_card.value_label.config(
                    text="Недоступна"
                )
                self.ram_card.detail_label.config(text="")

            self.os_card.value_label.config(
                text=platform.system()
            )
            self.os_card.detail_label.config(
                text=f"{platform.release()} · {platform.machine()}"
            )

            self.render_disks()

            self.status.config(
                text=(
                    f"Обновлено: {datetime.now():%d.%m.%Y %H:%M:%S}"
                    "  |  Автообновление каждые 5 секунд"
                )
            )

        except Exception as error:
            self.status.config(
                text=f"Ошибка обновления: {error}",
                fg=RED,
            )

    def render_disks(self):
        for widget in self.disk_frame.winfo_children():
            widget.destroy()

        self.disk_count.config(
            text=f"Найдено дисков: {len(self.disks)}"
        )

        if not self.disks:
            tk.Label(
                self.disk_frame,
                text="Накопители не обнаружены",
                bg=BG,
                fg=MUTED,
                font=("Segoe UI", 11),
            ).pack(anchor="w", pady=12)
            return

        for disk in self.disks:
            percent = disk["percent"]

            if percent >= 90:
                color = RED
                warning = "⚠ ВНИМАНИЕ: диск заполнен более чем на 90%"
            elif percent >= 80:
                color = YELLOW
                warning = "Мало свободного места"
            else:
                color = GREEN
                warning = "Состояние: нормально"

            card = tk.Frame(
                self.disk_frame,
                bg=PANEL,
                padx=14,
                pady=10,
            )
            card.pack(fill="x", pady=5)

            top = tk.Frame(card, bg=PANEL)
            top.pack(fill="x")

            tk.Label(
                top,
                text=disk["name"],
                bg=PANEL,
                fg=TEXT,
                font=("Segoe UI", 12, "bold"),
            ).pack(side="left")

            tk.Label(
                top,
                text=f"{percent:.1f}% занято",
                bg=PANEL,
                fg=color,
                font=("Segoe UI", 10, "bold"),
            ).pack(side="right")

            bar = ttk.Progressbar(
                card,
                style="Dark.Horizontal.TProgressbar",
                maximum=100,
                value=percent,
                mode="determinate",
            )
            bar.pack(fill="x", pady=(9, 7))

            # Цвет каждой полосы соответствует состоянию диска.
            style_name = f"Disk{disk['name'].replace(':', '')}.Horizontal.TProgressbar"

            ttk.Style().configure(
                style_name,
                troughcolor=PANEL_LIGHT,
                background=color,
                bordercolor=PANEL_LIGHT,
                lightcolor=color,
                darkcolor=color,
            )
            bar.configure(style=style_name)

            tk.Label(
                card,
                text=(
                    f"Свободно: {gb(disk['free'])}  |  "
                    f"Занято: {gb(disk['used'])}  |  "
                    f"Всего: {gb(disk['total'])}"
                ),
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 9),
            ).pack(anchor="w")

            tk.Label(
                card,
                text=warning,
                bg=PANEL,
                fg=color,
                font=("Segoe UI", 9, "bold"),
            ).pack(anchor="w", pady=(5, 0))

    def auto_refresh(self):
        if not self.root.winfo_exists():
            return

        self.refresh()
        self.root.after(5000, self.auto_refresh)

    def save_report(self):
        path = filedialog.asksaveasfilename(
            title="Сохранить диагностический отчёт",
            defaultextension=".txt",
            initialfile="pc_diagnostic_v3_report.txt",
            filetypes=[("Текстовые файлы", "*.txt")],
        )

        if not path:
            return

        lines = [
            "PC DIAGNOSTIC TOOL v3",
            f"Дата: {datetime.now():%Y-%m-%d %H:%M:%S}",
            "",
            "СИСТЕМА",
        ]

        for key, value in self.system_info.items():
            if key == "RAM":
                if value:
                    lines.append(
                        f"Оперативная память: {gb(value['total'])}"
                    )
                    lines.append(
                        f"Свободная память: {gb(value['available'])}"
                    )
                    lines.append(
                        f"Занято памяти: {value['used_percent']}%"
                    )
            else:
                lines.append(f"{key}: {value}")

        lines.extend(["", "ДИСКИ"])

        for disk in self.disks:
            warning = (
                "ВНИМАНИЕ: заполнение более 90%"
                if disk["percent"] >= 90
                else "Норма"
            )

            lines.append(
                f"{disk['name']} — всего {gb(disk['total'])}, "
                f"занято {gb(disk['used'])}, "
                f"свободно {gb(disk['free'])}, "
                f"заполнено {disk['percent']:.1f}%. {warning}"
            )

        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))

            messagebox.showinfo(
                "Отчёт сохранён",
                f"Файл успешно сохранён:\n{path}",
            )
        except OSError as error:
            messagebox.showerror(
                "Ошибка сохранения",
                str(error),
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = DiagnosticApp(root)
    root.mainloop()
