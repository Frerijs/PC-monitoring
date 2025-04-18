import psutil
import shutil
import time
import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk
import darkdetect
import ctypes

# ===== TERMINĀĻA FUNKCIJAS =====

def get_terminal_width():
    return shutil.get_terminal_size((80, 20)).columns

def get_bar(percent, width=30):
    filled = int(round((percent / (100) * width)))
    empty = width - filled
    return f"[{'█' * filled}{'-' * empty}]"

def get_color(percent):
    if percent < 40:
        return "\033[92m"
    elif percent < 70:
        return "\033[93m"
    else:
        return "\033[91m"

def get_status(percent):
    if percent < 40:
        return "Zema"
    elif percent < 70:
        return "Vidēja"
    else:
        return "Augsta"

spark_chars = "▁▂▃▄▅▆▇█"
def get_spark_char(value):
    idx = min(int(value / (100 / (len(spark_chars) - 1))), len(spark_chars) - 1)
    return spark_chars[idx]

cpu_history = []

def move_cursor(x, y):
    print(f"\033[{y};{x}H", end='')

def hide_cursor():
    print("\033[?25l", end='')

def show_cursor():
    print("\033[?25h", end='')

stop_flag = False

def key_listener():
    global stop_flag
    while not stop_flag:
        if input().strip().lower() == 'q':
            stop_flag = True

def get_gpu_usage():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        usage = int(output.strip().splitlines()[0])
        return usage
    except Exception:
        return None

def print_metric(label, percent, status, color, line):
    move_cursor(1, line)
    percent_str = f"{percent:>3d}%"
    bar = f"{get_bar(percent)} {percent_str}"
    print(f"{label:<9}{color}{bar.ljust(42)}\033[0m {status.ljust(6)}", end='')

def monitor():
    try:
        global stop_flag
        hide_cursor()
        print("\n" * 60)
        threading.Thread(target=key_listener, daemon=True).start()

        while not stop_flag:
            term_width = get_terminal_width()
            mem_percent = int(psutil.virtual_memory().percent)
            cpu_percent = int(psutil.cpu_percent(interval=0.5))
            core_percents = psutil.cpu_percent(interval=0.1, percpu=True)
            gpu_usage = get_gpu_usage()

            print_metric("💾 RAM :", mem_percent, get_status(mem_percent), get_color(mem_percent), 1)

            if gpu_usage is not None:
                print_metric("🎮 GPU :", gpu_usage, get_status(gpu_usage), get_color(gpu_usage), 2)
            else:
                move_cursor(1, 2)
                print(f"🎮 GPU :  {'[Nav pieejams GPU]'.ljust(42)} (Nav  )", end='')

            print_metric("🧠 CPU :", cpu_percent, get_status(cpu_percent), get_color(cpu_percent), 3)

            cpu_history.append(cpu_percent)
            if len(cpu_history) > 50:
                cpu_history.pop(0)
            sparkline = ''.join(get_spark_char(p) for p in cpu_history)
            move_cursor(1, 4)
            print("   " + sparkline.ljust(term_width), end='')

            for idx, percent in enumerate(core_percents):
                label = f"CPU {idx:2d}:"
                print_metric(label, int(percent), get_status(percent), get_color(percent), 5 + idx)

            move_cursor(1, 6 + len(core_percents))
            print("\033[90mNospied 'q' + Enter, lai izietu...\033[0m".ljust(term_width), end='')

            sys.stdout.flush()
            time.sleep(1)

        move_cursor(1, 7 + len(core_percents))
        show_cursor()
        print("\n\033[92mProgramma veiksmīgi apturēta.\033[0m")

    except KeyboardInterrupt:
        show_cursor()
        print("\n\033[0mApturēts ar Ctrl+C.")

# ===== GUI FUNKCIJAS =====

def start_gui():
    def update_metrics():
        mem_percent = int(psutil.virtual_memory().percent)
        cpu_percent = int(psutil.cpu_percent(interval=0.5))
        gpu_percent = get_gpu_usage()

        ram_var.set(mem_percent)
        cpu_var.set(cpu_percent)
        gpu_var.set(gpu_percent if gpu_percent is not None else 0)

        ram_label.config(text=f"RAM: {mem_percent}% ({get_status(mem_percent)})")
        cpu_label.config(text=f"CPU: {cpu_percent}% ({get_status(cpu_percent)})")
        gpu_label.config(
            text=f"GPU: {gpu_percent}% ({get_status(gpu_percent)})" if gpu_percent is not None else "GPU: Nav pieejams"
        )

        root.after(1000, update_metrics)

    def toggle_always_on_top():
        root.wm_attributes("-topmost", always_on_top_var.get())

    def toggle_dark_mode():
        if dark_mode_var.get():
            root.configure(bg='#2b2b2b')
            checkbox_frame.configure(bg='#2b2b2b')
            for label in [ram_label, cpu_label, gpu_label]:
                label.configure(bg='#2b2b2b', fg='white')
            pin_checkbox.configure(bg='#2b2b2b', fg='white', 
                                selectcolor='#1e1e1e',
                                activebackground='#2b2b2b',
                                activeforeground='white')
            dark_mode_checkbox.configure(bg='#2b2b2b', fg='white',
                                      selectcolor='#1e1e1e',
                                      activebackground='#2b2b2b',
                                      activeforeground='white')
            style.configure("TProgressbar", 
                          troughcolor='#1e1e1e',
                          background='#007acc')
            
            # Enable dark title bar
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            hwnd = get_parent(root.winfo_id())
            rendering_policy = ctypes.c_int(2)
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 
                               ctypes.byref(rendering_policy), 
                               ctypes.sizeof(rendering_policy))
        else:
            root.configure(bg='#f0f0f0')
            checkbox_frame.configure(bg='#f0f0f0')
            for label in [ram_label, cpu_label, gpu_label]:
                label.configure(bg='#f0f0f0', fg='black')
            pin_checkbox.configure(bg='#f0f0f0', fg='black',
                                selectcolor='white',
                                activebackground='#f0f0f0',
                                activeforeground='black')
            dark_mode_checkbox.configure(bg='#f0f0f0', fg='black',
                                      selectcolor='white',
                                      activebackground='#f0f0f0',
                                      activeforeground='black')
            style.configure("TProgressbar",
                          troughcolor='#e0e0e0',
                          background='#2196F3')
            
            # Disable dark title bar
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            hwnd = get_parent(root.winfo_id())
            rendering_policy = ctypes.c_int(0)
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 
                               ctypes.byref(rendering_policy), 
                               ctypes.sizeof(rendering_policy))

    root = tk.Tk()
    root.title("Sistēmas Monitors (GUI)")
    root.geometry("400x280")
    root.resizable(False, False)

    # Configure light theme colors by default
    root.configure(bg='#f0f0f0')
    
    style = ttk.Style(root)
    style.theme_use("default")
    style.configure("TProgressbar", 
                   thickness=20,
                   troughcolor='#e0e0e0',     # Changed to light mode color
                   background='#2196F3')       # Changed to light mode color
    
    ram_var = tk.IntVar()
    cpu_var = tk.IntVar()
    gpu_var = tk.IntVar()
    always_on_top_var = tk.BooleanVar(value=False)
    dark_mode_var = tk.BooleanVar(value=False)  # Changed from True to False

    # Remove the title text and update label styles
    ram_label = tk.Label(root, text="RAM:", font=("Arial", 12), bg='#f0f0f0', fg='black')
    ram_label.pack()
    ttk.Progressbar(root, variable=ram_var, maximum=100, length=350).pack(pady=5)

    cpu_label = tk.Label(root, text="CPU:", font=("Arial", 12), bg='#f0f0f0', fg='black')
    cpu_label.pack()
    ttk.Progressbar(root, variable=cpu_var, maximum=100, length=350).pack(pady=5)

    gpu_label = tk.Label(root, text="GPU:", font=("Arial", 12), bg='#f0f0f0', fg='black')
    gpu_label.pack()
    ttk.Progressbar(root, variable=gpu_var, maximum=100, length=350).pack(pady=5)

    # Add checkbox container frame with light theme
    checkbox_frame = tk.Frame(root, bg='#f0f0f0')
    checkbox_frame.pack(pady=10)

    pin_checkbox = tk.Checkbutton(checkbox_frame, 
                                text="📌 Vienmēr redzams (piespraust)", 
                                variable=always_on_top_var,
                                command=toggle_always_on_top, 
                                font=("Arial", 10),
                                bg='#f0f0f0',
                                fg='black',
                                selectcolor='white',
                                activebackground='#f0f0f0',
                                activeforeground='black')
    pin_checkbox.pack(pady=5)

    dark_mode_checkbox = tk.Checkbutton(checkbox_frame,
                                      text="🌙 Tumšais režīms",
                                      variable=dark_mode_var,
                                      command=toggle_dark_mode,
                                      font=("Arial", 10),
                                      bg='#f0f0f0',
                                      fg='black',
                                      selectcolor='white',
                                      activebackground='#f0f0f0',
                                      activeforeground='black')
    dark_mode_checkbox.pack(pady=5)

    update_metrics()
    root.mainloop()

# ===== PALAIŠANA =====

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        start_gui()
    else:
        monitor()
