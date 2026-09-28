import os
import re
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

IS_WIN = sys.platform.startswith("win")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WIN else 0


def find_ffmpeg():
    """Ищет ffmpeg: внутри exe (PyInstaller), рядом с программой, затем в PATH."""
    name = "ffmpeg.exe" if IS_WIN else "ffmpeg"
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, name))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), name))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return name  # надеемся, что он в PATH


def to_seconds(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTS → MP4 конвертер")
        self.geometry("680x520")
        self.minsize(620, 480)

        self.ffmpeg = find_ffmpeg()
        self.files = []
        self.proc = None
        self.stop_flag = False

        self.out_dir = tk.StringVar()
        self.mode = tk.StringVar(value="fast")
        self.crf = tk.IntVar(value=20)
        self.deint = tk.BooleanVar(value=False)
        self.same_dir = tk.BooleanVar(value=True)

        self.build_ui()

    def build_ui(self):
        pad = {"padx": 10, "pady": 5}

        top = ttk.Frame(self)
        top.pack(fill="both", expand=True, **pad)

        ttk.Label(top, text="Файлы MTS:").pack(anchor="w")
        lf = ttk.Frame(top)
        lf.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(lf, selectmode="extended", height=8)
        sb = ttk.Scrollbar(lf, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        bf = ttk.Frame(top)
        bf.pack(fill="x", pady=5)
        ttk.Button(bf, text="Добавить файлы…", command=self.add_files).pack(side="left")
        ttk.Button(bf, text="Добавить папку…", command=self.add_folder).pack(side="left", padx=5)
        ttk.Button(bf, text="Удалить выбранные", command=self.remove_selected).pack(side="left")
        ttk.Button(bf, text="Очистить", command=self.clear).pack(side="left", padx=5)

        # Папка вывода
        of = ttk.LabelFrame(self, text="Куда сохранять")
        of.pack(fill="x", **pad)
        ttk.Checkbutton(of, text="В ту же папку, где лежит исходник", variable=self.same_dir,
                        command=self.toggle_out).pack(anchor="w", padx=5, pady=2)
        row = ttk.Frame(of)
        row.pack(fill="x", padx=5, pady=3)
        self.out_entry = ttk.Entry(row, textvariable=self.out_dir, state="disabled")
        self.out_entry.pack(side="left", fill="x", expand=True)
        self.out_btn = ttk.Button(row, text="Обзор…", command=self.choose_out, state="disabled")
        self.out_btn.pack(side="left", padx=5)

        # Настройки
        sf = ttk.LabelFrame(self, text="Режим")
        sf.pack(fill="x", **pad)
        ttk.Radiobutton(sf, text="Быстро — видео без перекодирования (без потери качества)",
                        variable=self.mode, value="fast", command=self.toggle_mode).pack(anchor="w", padx=5)
        ttk.Radiobutton(sf, text="Перекодирование H.264 (меньше размер, можно убрать «гребёнку»)",
                        variable=self.mode, value="enc", command=self.toggle_mode).pack(anchor="w", padx=5)
        qf = ttk.Frame(sf)
        qf.pack(fill="x", padx=25, pady=3)
        ttk.Label(qf, text="Качество CRF (меньше = лучше, 18–28):").pack(side="left")
        self.crf_spin = ttk.Spinbox(qf, from_=16, to=32, width=5, textvariable=self.crf, state="disabled")
        self.crf_spin.pack(side="left", padx=5)
        self.deint_chk = ttk.Checkbutton(qf, text="Убрать чересстрочность (deinterlace)",
                                         variable=self.deint, state="disabled")
        self.deint_chk.pack(side="left", padx=10)

        # Прогресс
        pf = ttk.Frame(self)
        pf.pack(fill="x", **pad)
        self.status = ttk.Label(pf, text="Готов к работе")
        self.status.pack(anchor="w")
        self.file_bar = ttk.Progressbar(pf, maximum=100)
        self.file_bar.pack(fill="x", pady=2)
        self.total_bar = ttk.Progressbar(pf, maximum=100)
        self.total_bar.pack(fill="x", pady=2)

        bt = ttk.Frame(self)
        bt.pack(fill="x", **pad)
        self.start_btn = ttk.Button(bt, text="Конвертировать", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(bt, text="Стоп", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

    # ---------- UI helpers ----------
    def toggle_out(self):
        st = "disabled" if self.same_dir.get() else "normal"
        self.out_entry.config(state=st)
        self.out_btn.config(state=st)

    def toggle_mode(self):
        st = "normal" if self.mode.get() == "enc" else "disabled"
        self.crf_spin.config(state=st)
        self.deint_chk.config(state=st)

    def choose_out(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir.set(d)

    def add_paths(self, paths):
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", p)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("MTS / M2TS", "*.mts *.m2ts *.MTS *.M2TS"), ("Все файлы", "*.*")])
        self.add_paths(paths)

    def add_folder(self):
        d = filedialog.askdirectory()
        if not d:
            return
        found = []
        for root, _, names in os.walk(d):
            for n in sorted(names):
                if n.lower().endswith((".mts", ".m2ts")):
                    found.append(os.path.join(root, n))
        if not found:
            messagebox.showinfo("Нет файлов", "В папке не найдено MTS/M2TS файлов.")
        self.add_paths(found)

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i)
            del self.files[i]

    def clear(self):
        self.listbox.delete(0, "end")
        self.files.clear()

    # ---------- Конвертация ----------
    def start(self):
        if not self.files:
            messagebox.showwarning("Нет файлов", "Добавьте хотя бы один файл.")
            return
        if not self.same_dir.get() and not self.out_dir.get():
            messagebox.showwarning("Папка", "Выберите папку для сохранения.")
            return
        self.stop_flag = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.worker, daemon=True).start()

    def stop(self):
        self.stop_flag = True
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    def ui(self, fn, *a):
        self.after(0, lambda: fn(*a))

    def build_cmd(self, src, dst):
        cmd = [self.ffmpeg, "-y", "-hide_banner", "-i", src, "-map", "0:v:0", "-map", "0:a?"]
        if self.mode.get() == "fast":
            cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
        else:
            if self.deint.get():
                cmd += ["-vf", "yadif"]
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(self.crf.get()),
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"]
        cmd += ["-movflags", "+faststart", dst]
        return cmd

    def worker(self):
        total = len(self.files)
        ok, failed = 0, []
        for idx, src in enumerate(list(self.files)):
            if self.stop_flag:
                break
            base = os.path.splitext(os.path.basename(src))[0] + ".mp4"
            out_dir = os.path.dirname(src) if self.same_dir.get() else self.out_dir.get()
            dst = os.path.join(out_dir, base)
            if os.path.abspath(dst) == os.path.abspath(src):
                failed.append(src)
                continue

            self.ui(self.status.config, {"text": f"[{idx + 1}/{total}] {os.path.basename(src)}"})
            self.ui(self.file_bar.config, {"value": 0})
            try:
                self.proc = subprocess.Popen(
                    self.build_cmd(src, dst), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    creationflags=NO_WINDOW)
            except FileNotFoundError:
                self.ui(messagebox.showerror, "ffmpeg не найден",
                        "Положите ffmpeg.exe рядом с программой или добавьте его в PATH.")
                break

            duration, buf, tail = None, b"", ""
            while True:
                ch = self.proc.stdout.read(1)
                if not ch:
                    break
                if ch in (b"\r", b"\n"):
                    line = buf.decode("utf-8", "ignore")
                    buf = b""
                    tail = line or tail
                    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", line)
                    if m and duration is None:
                        duration = to_seconds(*m.groups())
                    m = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
                    if m and duration:
                        pct = min(100, to_seconds(*m.groups()) / duration * 100)
                        self.ui(self.file_bar.config, {"value": pct})
                        self.ui(self.total_bar.config, {"value": (idx + pct / 100) / total * 100})
                else:
                    buf += ch
            self.proc.wait()

            if self.proc.returncode == 0:
                ok += 1
            else:
                failed.append(src)
                if os.path.exists(dst):
                    try:
                        os.remove(dst)
                    except OSError:
                        pass
            self.ui(self.total_bar.config, {"value": (idx + 1) / total * 100})

        self.ui(self.finish, ok, failed)

    def finish(self, ok, failed):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        if self.stop_flag:
            self.status.config(text="Остановлено")
            return
        self.status.config(text=f"Готово: {ok} успешно, {len(failed)} с ошибкой")
        if failed:
            messagebox.showwarning("Есть ошибки", "Не удалось конвертировать:\n" + "\n".join(failed))
        else:
            messagebox.showinfo("Готово", f"Сконвертировано файлов: {ok}")


if __name__ == "__main__":
    App().mainloop()
