import os
import sys
import threading
import subprocess
import shlex
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ./ffmpeg/ffmpeg.exe
# ./ffmpeg/ffprobe.exe
# ./saves/

ROOT = Path(__file__).parent
FFMPEG_DIR = ROOT / "ffmpeg"
if getattr(sys, 'frozen', False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).parent
SAVES_DIR.mkdir(exist_ok=True)

if (FFMPEG_DIR / "ffmpeg.exe").exists() or (FFMPEG_DIR / "ffmpeg").exists():
    if (FFMPEG_DIR / "ffmpeg.exe").exists():
        FFMPEG_BIN = str(FFMPEG_DIR / "ffmpeg.exe")
    else:
        FFMPEG_BIN = str(FFMPEG_DIR / "ffmpeg")
else:
    FFMPEG_BIN = "ffmpeg" 

if (FFMPEG_DIR / "ffprobe.exe").exists() or (FFMPEG_DIR / "ffprobe").exists():
    if (FFMPEG_DIR / "ffprobe.exe").exists():
        FFPROBE_BIN = str(FFMPEG_DIR / "ffprobe.exe")
    else:
        FFPROBE_BIN = str(FFMPEG_DIR / "ffprobe")
else:
    FFPROBE_BIN = "ffprobe"


def unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    i = 1
    while True:
        candidate = dest.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def run_subprocess(cmd, write_log=None):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False)
    for line in p.stdout:
        if write_log:
            write_log(line)
    p.wait()
    return p.returncode


def ffprobe_duration(path):
    """Получаем длительность файла в секундах с помощью ffprobe. Вернёт float или None."""
    cmd = [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return float(out.strip())
    except Exception:
        return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VideoCodexConvertor DEV 1.03")
        self.geometry("780x520")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.conv_frame = ttk.Frame(self.notebook)
        self.comp_prec_frame = ttk.Frame(self.notebook)
        self.comp_fast_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.conv_frame, text="конвертация")
        self.notebook.add(self.comp_prec_frame, text="сжатие (точное)")
        self.notebook.add(self.comp_fast_frame, text="сжатие (быстрое)")

        self._build_conversion_tab()
        self._build_compression_precise_tab()
        self._build_compression_fast_tab()

        log_label = ttk.Label(self, text="Лог:")
        log_label.pack(anchor=tk.W, padx=12)
        self.log_text = tk.Text(self, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=False, padx=12, pady=(0,12))
        self.log_text.configure(state=tk.DISABLED)

    def write_log(self, text):
        def _write():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.after(0, _write)

    def _build_conversion_tab(self):
        f = self.conv_frame
        padx = 8; pady = 6

        row = ttk.Frame(f)
        row.pack(fill=tk.X, padx=12, pady=pady)
        ttk.Label(row, text="Файл:").pack(side=tk.LEFT)
        self.conv_input_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.conv_input_var, width=60).pack(side=tk.LEFT, padx=6)
        ttk.Button(row, text="Обзор", command=self.conv_browse).pack(side=tk.LEFT)

        row2 = ttk.Frame(f)
        row2.pack(fill=tk.X, padx=12, pady=pady)
        ttk.Label(row2, text="Выходное расширение (без точки), например mp4, png, jpg, webp ").pack(side=tk.LEFT)
        self.conv_ext_var = tk.StringVar(value="mp4")
        ttk.Entry(row2, textvariable=self.conv_ext_var, width=10).pack(side=tk.LEFT, padx=6)

        row3 = ttk.Frame(f)
        row3.pack(fill=tk.X, padx=12, pady=pady)
        self.conv_btn = ttk.Button(row3, text="Конвертировать", command=self.start_conversion)
        self.conv_btn.pack(side=tk.LEFT)

        ttk.Label(row3, text="").pack(side=tk.LEFT)

    def _build_compression_precise_tab(self):
        f = self.comp_prec_frame
        padx = 8; pady = 6

        row = ttk.Frame(f)
        row.pack(fill=tk.X, padx=12, pady=pady)
        ttk.Label(row, text="Видео файл:").pack(side=tk.LEFT)
        self.comp_prec_input_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.comp_prec_input_var, width=60).pack(side=tk.LEFT, padx=6)
        ttk.Button(row, text="Обзор", command=self.comp_prec_browse).pack(side=tk.LEFT)

        row2 = ttk.Frame(f)
        row2.pack(fill=tk.X, padx=12, pady=pady)
        ttk.Label(row2, text="Желаемый размер (МБ):").pack(side=tk.LEFT)
        self.comp_prec_size_var = tk.StringVar(value="10")
        ttk.Entry(row2, textvariable=self.comp_prec_size_var, width=10).pack(side=tk.LEFT, padx=6)

        ttk.Label(row2, text="Аудио-битрейт (кбит/с, по умолчанию 128):").pack(side=tk.LEFT, padx=12)
        self.comp_prec_audio_var = tk.StringVar(value="128")
        ttk.Entry(row2, textvariable=self.comp_prec_audio_var, width=6).pack(side=tk.LEFT)

        row3 = ttk.Frame(f)
        row3.pack(fill=tk.X, padx=12, pady=pady)
        self.comp_prec_btn = ttk.Button(row3, text="Сжать", command=self.start_compression_precise)
        self.comp_prec_btn.pack(side=tk.LEFT)

        ttk.Label(row3, text="   (двухпроходное кодирование более точное, но медленее кодируется)").pack(side=tk.LEFT)

    def _build_compression_fast_tab(self):
        f = self.comp_fast_frame
        padx = 8; pady = 6

        row = ttk.Frame(f)
        row.pack(fill=tk.X, padx=12, pady=pady)
        ttk.Label(row, text="Видео файл:").pack(side=tk.LEFT)
        self.comp_fast_input_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.comp_fast_input_var, width=60).pack(side=tk.LEFT, padx=6)
        ttk.Button(row, text="Обзор", command=self.comp_fast_browse).pack(side=tk.LEFT)

        row2 = ttk.Frame(f)
        row2.pack(fill=tk.X, padx=12, pady=pady)
        ttk.Label(row2, text="Желаемый размер (МБ):").pack(side=tk.LEFT)
        self.comp_fast_size_var = tk.StringVar(value="10")
        ttk.Entry(row2, textvariable=self.comp_fast_size_var, width=10).pack(side=tk.LEFT, padx=6)

        ttk.Label(row2, text="Аудио-битрейт (по умолчанию 128):").pack(side=tk.LEFT, padx=12)
        self.comp_fast_audio_var = tk.StringVar(value="128")
        ttk.Entry(row2, textvariable=self.comp_fast_audio_var, width=6).pack(side=tk.LEFT)

        row3 = ttk.Frame(f)
        row3.pack(fill=tk.X, padx=12, pady=pady)
        self.comp_fast_btn = ttk.Button(row3, text="Сжать", command=self.start_compression_fast)
        self.comp_fast_btn.pack(side=tk.LEFT)

        ttk.Label(row3, text="   (одно-проходное кодирование быстрое но менее точное)").pack(side=tk.LEFT)

    def conv_browse(self):
        p = filedialog.askopenfilename(title="Выберите файл для конвертации")
        if p:
            self.conv_input_var.set(p)

    def comp_prec_browse(self):
        p = filedialog.askopenfilename(title="Выберите видео для сжатия (точное)")
        if p:
            self.comp_prec_input_var.set(p)

    def comp_fast_browse(self):
        p = filedialog.askopenfilename(title="Выберите видео для сжатия (быстрое)")
        if p:
            self.comp_fast_input_var.set(p)

    def start_conversion(self):
        input_path = self.conv_input_var.get().strip()
        ext = self.conv_ext_var.get().strip().lstrip('.')
        if not input_path or not ext:
            messagebox.showerror("Ошибка", "Выберите файл и укажите выходное расширение")
            return
        self.conv_btn.configure(state=tk.DISABLED)
        thread = threading.Thread(target=self._conversion_worker, args=(input_path, ext), daemon=True)
        thread.start()

    def _conversion_worker(self, input_path, ext):
        try:
            inp = Path(input_path)
            if not inp.exists():
                self.write_log(f"Файл не найден: {input_path}")
                return
            out_name = inp.stem + '.' + ext
            out_path = SAVES_DIR / out_name
            out_path = unique_path(out_path)

            cmd_copy = [FFMPEG_BIN, '-y', '-i', str(inp), '-c', 'copy', str(out_path)]
            self.write_log(f"Попытка копирования потоков: {' '.join(cmd_copy)}")
            rc = run_subprocess(cmd_copy, write_log=self.write_log)
            if rc == 0 and out_path.exists():
                self.write_log(f"Готово (копирование): {out_path}")
                return

            self.write_log("Копирование не сработало — выполняем перекодировку (libx264/aac)")
            img_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'}
            if inp.suffix.lower() in img_exts:
                cmd_img = [FFMPEG_BIN, '-y', '-i', str(inp), str(out_path)]
                self.write_log(f"Команда: {' '.join(cmd_img)}")
                run_subprocess(cmd_img, write_log=self.write_log)
            else:
                cmd_enc = [FFMPEG_BIN, '-y', '-i', str(inp), '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-c:a', 'aac', '-b:a', '128k', str(out_path)]
                self.write_log(f"Команда: {' '.join(cmd_enc)}")
                run_subprocess(cmd_enc, write_log=self.write_log)

            if out_path.exists():
                self.write_log(f"Готово (перекодировка): {out_path}")
            else:
                self.write_log("Что-то пошло не так — выходной файл не найден")
        except Exception as e:
            self.write_log(f"Ошибка: {e}")
        finally:
            self.after(0, lambda: self.conv_btn.configure(state=tk.NORMAL))

    def start_compression_precise(self):
        input_path = self.comp_prec_input_var.get().strip()
        size_mb = self.comp_prec_size_var.get().strip()
        audio_kbit = self.comp_prec_audio_var.get().strip()
        if not input_path:
            messagebox.showerror("Ошибка", "Выберите видеофайл для сжатия")
            return
        try:
            size_mb = float(size_mb)
            audio_kbit = int(audio_kbit)
        except Exception:
            messagebox.showerror("Ошибка", "Неверное значение размера или аудио-битрейта")
            return
        self.comp_prec_btn.configure(state=tk.DISABLED)
        thread = threading.Thread(target=self._compression_worker_precise, args=(input_path, size_mb, audio_kbit), daemon=True)
        thread.start()

    def _compression_worker_precise(self, input_path, size_mb, audio_kbit):
        try:
            inp = Path(input_path)
            if not inp.exists():
                self.write_log(f"Файл не найден: {input_path}")
                return

            duration = ffprobe_duration(inp)
            if not duration or duration <= 0:
                self.write_log("Не удалось получить длительность видео (ffprobe)")
                return

            target_bytes = size_mb * 1024 * 1024
            audio_bps = audio_kbit * 1000
            total_bps = (target_bytes * 8) / duration
            video_bps = total_bps - audio_bps
            if video_bps < 10000:
                self.write_log("Рассчитанный видеобитрейт слишком мал — уменьшите аудио-битрейт или увеличьте размер файла")
                video_bps = max(int(total_bps * 0.9), 10000)

            video_bitrate = str(int(video_bps))
            audio_bitrate = f"{audio_kbit}k"

            out_name = inp.stem + f"_compressed_precise{inp.suffix}"
            out_path = SAVES_DIR / out_name
            out_path = unique_path(out_path)

            self.write_log(f"Длительность: {duration:.2f} s")
            self.write_log(f"Целевой размер: {size_mb} MB -> video_bitrate={video_bitrate} bps, audio={audio_bitrate}")

            null_dev = "NUL" if os.name == 'nt' else "/dev/null"

            cmd1 = [FFMPEG_BIN, '-y', '-i', str(inp), '-c:v', 'libx264', '-b:v', video_bitrate, '-pass', '1', '-an', '-f', 'mp4', null_dev]
            self.write_log(f"Первый проход: {' '.join(cmd1)}")
            rc1 = run_subprocess(cmd1, write_log=self.write_log)
            if rc1 != 0:
                self.write_log("Первый проход вернул код != 0, но продолжаем вторым проходом (возможно предупреждения)")

            cmd2 = [FFMPEG_BIN, '-y', '-i', str(inp), '-c:v', 'libx264', '-b:v', video_bitrate, '-pass', '2', '-c:a', 'aac', '-b:a', audio_bitrate, str(out_path)]
            self.write_log(f"Второй проход: {' '.join(cmd2)}")
            rc2 = run_subprocess(cmd2, write_log=self.write_log)

            for f in ROOT.iterdir():
                try:
                    if f.name.startswith('ffmpeg2pass') or 'ffmpeg2pass' in f.name or (f.suffix == '.log' and 'ffmpeg' in f.name):
                        f.unlink()
                except Exception:
                    pass

            if out_path.exists():
                self.write_log(f"Готово: {out_path}")
            else:
                self.write_log("Не удалось создать выходной файл.")

        except Exception as e:
            self.write_log(f"Ошибка: {e}")
        finally:
            self.after(0, lambda: self.comp_prec_btn.configure(state=tk.NORMAL))

    def start_compression_fast(self):
        input_path = self.comp_fast_input_var.get().strip()
        size_mb = self.comp_fast_size_var.get().strip()
        audio_kbit = self.comp_fast_audio_var.get().strip()
        if not input_path:
            messagebox.showerror("Ошибка", "Выберите видеофайл для сжатия")
            return
        try:
            size_mb = float(size_mb)
            audio_kbit = int(audio_kbit)
        except Exception:
            messagebox.showerror("Ошибка", "Неверное значение размера или аудио-битрейта")
            return
        self.comp_fast_btn.configure(state=tk.DISABLED)
        thread = threading.Thread(target=self._compression_worker_fast, args=(input_path, size_mb, audio_kbit), daemon=True)
        thread.start()

    def _compression_worker_fast(self, input_path, size_mb, audio_kbit):
        try:
            inp = Path(input_path)
            if not inp.exists():
                self.write_log(f"Файл не найден: {input_path}")
                return

            duration = ffprobe_duration(inp)
            if not duration or duration <= 0:
                self.write_log("Не удалось получить длительность видео (ffprobe)")
                return

            target_bytes = size_mb * 1024 * 1024
            audio_bps = audio_kbit * 1000
            total_bps = (target_bytes * 8) / duration
            video_bps = total_bps - audio_bps
            if video_bps < 10000:
                self.write_log("Рассчитанный видеобитрейт слишком мал — уменьшите аудио-битрейт или увеличьте размер файла")
                video_bps = max(int(total_bps * 0.9), 10000)

            video_bitrate = str(int(video_bps))
            audio_bitrate = f"{audio_kbit}k"

            out_name = inp.stem + f"_compressed_fast{inp.suffix}"
            out_path = SAVES_DIR / out_name
            out_path = unique_path(out_path)

            self.write_log(f"Длительность: {duration:.2f} s")
            self.write_log(f"Целевой размер: {size_mb} MB -> video_bitrate={video_bitrate} bps, audio={audio_bitrate}")

            cmd = [FFMPEG_BIN, '-y', '-i', str(inp), '-c:v', 'libx264', '-b:v', video_bitrate, '-preset', 'fast', '-c:a', 'aac', '-b:a', audio_bitrate, str(out_path)]
            self.write_log(f"Команда (быстрое): {' '.join(cmd)}")
            rc = run_subprocess(cmd, write_log=self.write_log)

            if out_path.exists():
                self.write_log(f"Готово: {out_path}")
            else:
                self.write_log("Не удалось создать выходной файл")

        except Exception as e:
            self.write_log(f"Ошибка: {e}")
        finally:
            self.after(0, lambda: self.comp_fast_btn.configure(state=tk.NORMAL))


if __name__ == '__main__':
    app = App()
    app.mainloop()
