import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta
import math
import random

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄专注")
        self.root.geometry("420x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d1117")
        
        self.init_settings()
        self.init_state()
        self.load_data()
        self.setup_styles()
        self.build_ui()
        self.update_display()
        
    def init_settings(self):
        self.settings = {
            "work_duration": 25,
            "short_break": 5,
            "long_break": 15,
            "cycles_before_long": 4,
            "sound_enabled": True,
            "auto_start_break": False,
            "auto_start_work": False,
            "volume": 50
        }
        
    def init_state(self):
        self.time_left = self.settings["work_duration"] * 60
        self.is_running = False
        self.is_paused = False
        self.current_mode = "work"
        self.completed_pomodoros = 0
        self.total_focus_seconds = 0
        self.current_task = None
        self.tasks = []
        self.history = []
        self.session_start = None
        self.quotes = [
            "专注当下，成就未来",
            "千里之行，始于足下", 
            "保持专注，保持高效",
            "每一个番茄都是进步",
            "专注是一种力量",
            "小步快跑，持续进步"
        ]
        
    def setup_styles(self):
        self.colors = {
            "bg": "#0d1117",
            "card": "#161b22",
            "border": "#30363d",
            "text": "#c9d1d9",
            "text_dim": "#8b949e",
            "accent": "#58a6ff",
            "work": "#f85149",
            "work_light": "#ff7b72",
            "break": "#3fb950",
            "break_light": "#7ee787",
            "long_break": "#a371f7",
            "long_break_light": "#d2a8ff"
        }
        
    def build_ui(self):
        self.build_header()
        self.build_timer_section()
        self.build_controls()
        self.build_mode_selector()
        self.build_task_section()
        self.build_stats_section()
        self.build_footer()
        
    def build_header(self):
        header = tk.Frame(self.root, bg=self.colors["card"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.colors["card"])
        title_frame.pack(side="left", padx=15, pady=10)
        
        tk.Label(
            title_frame,
            text="🍅",
            font=("Segoe UI Emoji", 18),
            bg=self.colors["card"],
            fg=self.colors["work"]
        ).pack(side="left")
        
        tk.Label(
            title_frame,
            text=" 番茄专注",
            font=("Microsoft YaHei", 14, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left")
        
        settings_btn = tk.Label(
            header,
            text="⚙",
            font=("Segoe UI", 16),
            bg=self.colors["card"],
            fg=self.colors["text_dim"],
            cursor="hand2"
        )
        settings_btn.pack(side="right", padx=15)
        settings_btn.bind("<Button-1>", lambda e: self.open_settings())
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(fg=self.colors["accent"]))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(fg=self.colors["text_dim"]))
        
    def build_timer_section(self):
        timer_frame = tk.Frame(self.root, bg=self.colors["bg"])
        timer_frame.pack(fill="x", pady=20)
        
        self.mode_label = tk.Label(
            timer_frame,
            text="专注时间",
            font=("Microsoft YaHei", 12),
            bg=self.colors["bg"],
            fg=self.colors["work"]
        )
        self.mode_label.pack()
        
        canvas_frame = tk.Frame(timer_frame, bg=self.colors["bg"])
        canvas_frame.pack(pady=10)
        
        self.timer_canvas = tk.Canvas(
            canvas_frame,
            width=200,
            height=200,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        self.timer_canvas.pack()
        
        self.time_label = tk.Label(
            timer_frame,
            text="25:00",
            font=("Consolas", 48, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        )
        self.time_label.place(relx=0.5, rely=0.35, anchor="center")
        
        self.quote_label = tk.Label(
            timer_frame,
            text=random.choice(self.quotes),
            font=("Microsoft YaHei", 10, "italic"),
            bg=self.colors["bg"],
            fg=self.colors["text_dim"],
            wraplength=350
        )
        self.quote_label.pack(pady=(100, 0))
        
    def build_controls(self):
        controls = tk.Frame(self.root, bg=self.colors["bg"])
        controls.pack(pady=10)
        
        btn_config = [
            ("▶ 开始", self.start_timer, self.colors["accent"]),
            ("⏸ 暂停", self.pause_timer, self.colors["work"]),
            ("⏹ 重置", self.reset_timer, self.colors["border"])
        ]
        
        for text, cmd, color in btn_config:
            btn = tk.Label(
                controls,
                text=text,
                font=("Microsoft YaHei", 10),
                bg=color,
                fg="white",
                padx=18,
                pady=8,
                cursor="hand2"
            )
            btn.pack(side="left", padx=5)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.config(relief="raised"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(relief="flat"))
            
    def build_mode_selector(self):
        mode_frame = tk.Frame(self.root, bg=self.colors["bg"])
        mode_frame.pack(pady=10)
        
        modes = [
            ("🍅 专注", "work", self.settings["work_duration"]),
            ("☕ 短休", "short_break", self.settings["short_break"]),
            ("🛋 长休", "long_break", self.settings["long_break"])
        ]
        
        self.mode_buttons = {}
        for text, mode, duration in modes:
            btn = tk.Label(
                mode_frame,
                text=text,
                font=("Microsoft YaHei", 9),
                bg=self.colors["card"],
                fg=self.colors["text_dim"],
                padx=12,
                pady=6,
                cursor="hand2"
            )
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, m=mode, d=duration: self.switch_mode(m, d))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors["border"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors["card"]))
            self.mode_buttons[mode] = btn
            
        self.update_mode_buttons()
        
    def build_task_section(self):
        task_card = tk.Frame(self.root, bg=self.colors["card"], padx=15, pady=12)
        task_card.pack(fill="x", padx=20, pady=5)
        
        header = tk.Frame(task_card, bg=self.colors["card"])
        header.pack(fill="x")
        
        tk.Label(
            header,
            text="📋 当前任务",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left")
        
        self.current_task_label = tk.Label(
            task_card,
            text="点击下方选择任务",
            font=("Microsoft YaHei", 10),
            bg=self.colors["card"],
            fg=self.colors["text_dim"]
        )
        self.current_task_label.pack(anchor="w", pady=(8, 5))
        
        list_frame = tk.Frame(task_card, bg=self.colors["card"])
        list_frame.pack(fill="x")
        
        self.task_listbox = tk.Listbox(
            list_frame,
            height=3,
            font=("Microsoft YaHei", 9),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="white",
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.colors["border"],
            highlightbackground=self.colors["border"]
        )
        self.task_listbox.pack(side="left", fill="both", expand=True)
        self.task_listbox.bind("<<ListboxSelect>>", self.on_task_select)
        
        scrollbar = tk.Scrollbar(list_frame, command=self.task_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.task_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = tk.Frame(task_card, bg=self.colors["card"])
        btn_frame.pack(fill="x", pady=(10, 0))
        
        actions = [
            ("+ 添加", self.add_task, self.colors["accent"]),
            ("✓ 完成", self.complete_task, self.colors["break"]),
            ("✕ 删除", self.delete_task, self.colors["work"])
        ]
        
        for text, cmd, color in actions:
            btn = tk.Label(
                btn_frame,
                text=text,
                font=("Microsoft YaHei", 9),
                bg=color,
                fg="white",
                padx=10,
                pady=4,
                cursor="hand2"
            )
            btn.pack(side="left", padx=3)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            
        self.refresh_task_list()
        
    def build_stats_section(self):
        stats_card = tk.Frame(self.root, bg=self.colors["card"], padx=15, pady=12)
        stats_card.pack(fill="x", padx=20, pady=5)
        
        tk.Label(
            stats_card,
            text="📊 今日统计",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w")
        
        stats_row = tk.Frame(stats_card, bg=self.colors["card"])
        stats_row.pack(fill="x", pady=(10, 0))
        
        self.pomodoro_count_label = tk.Label(
            stats_row,
            text="🍅 0 个番茄",
            font=("Microsoft YaHei", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.pomodoro_count_label.pack(side="left")
        
        self.focus_time_label = tk.Label(
            stats_row,
            text="⏱ 0 分钟专注",
            font=("Microsoft YaHei", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.focus_time_label.pack(side="right")
        
        cycle_frame = tk.Frame(stats_card, bg=self.colors["card"])
        cycle_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(
            cycle_frame,
            text="周期进度:",
            font=("Microsoft YaHei", 9),
            bg=self.colors["card"],
            fg=self.colors["text_dim"]
        ).pack(side="left")
        
        self.cycle_indicators = []
        for i in range(4):
            indicator = tk.Label(
                cycle_frame,
                text="○",
                font=("Segoe UI", 12),
                bg=self.colors["card"],
                fg=self.colors["border"]
            )
            indicator.pack(side="left", padx=2)
            self.cycle_indicators.append(indicator)
            
    def build_footer(self):
        footer = tk.Frame(self.root, bg=self.colors["bg"])
        footer.pack(side="bottom", pady=10)
        
        tk.Label(
            footer,
            text="按 空格 开始/暂停 | R 重置",
            font=("Microsoft YaHei", 9),
            bg=self.colors["bg"],
            fg=self.colors["text_dim"]
        ).pack()
        
        self.root.bind("<space>", lambda e: self.toggle_timer())
        self.root.bind("<r>", lambda e: self.reset_timer())
        self.root.bind("<R>", lambda e: self.reset_timer())
        
    def draw_timer_circle(self):
        self.timer_canvas.delete("all")
        
        cx, cy = 100, 100
        radius = 85
        
        total_seconds = self.get_mode_duration() * 60
        progress = 1 - (self.time_left / total_seconds) if total_seconds > 0 else 0
        
        mode_colors = {
            "work": (self.colors["work"], self.colors["work_light"]),
            "short_break": (self.colors["break"], self.colors["break_light"]),
            "long_break": (self.colors["long_break"], self.colors["long_break_light"])
        }
        primary, light = mode_colors.get(self.current_mode, (self.colors["work"], self.colors["work_light"]))
        
        self.timer_canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            outline=self.colors["border"],
            width=6
        )
        
        if progress > 0:
            start_angle = 90
            extent = -progress * 360
            
            self.timer_canvas.create_arc(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                start=start_angle,
                extent=extent,
                outline=primary,
                width=6,
                style="arc"
            )
            
        self.timer_canvas.create_oval(
            cx - 6, cy - 6,
            cx + 6, cy + 6,
            fill=primary,
            outline=""
        )
        
    def get_mode_duration(self):
        durations = {
            "work": self.settings["work_duration"],
            "short_break": self.settings["short_break"],
            "long_break": self.settings["long_break"]
        }
        return durations.get(self.current_mode, 25)
        
    def get_mode_name(self):
        names = {
            "work": "专注时间",
            "short_break": "短休息",
            "long_break": "长休息"
        }
        return names.get(self.current_mode, "专注时间")
        
    def get_mode_color(self):
        colors = {
            "work": self.colors["work"],
            "short_break": self.colors["break"],
            "long_break": self.colors["long_break"]
        }
        return colors.get(self.current_mode, self.colors["work"])
        
    def update_display(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        self.mode_label.config(text=self.get_mode_name(), fg=self.get_mode_color())
        self.draw_timer_circle()
        self.update_stats()
        
    def update_mode_buttons(self):
        for mode, btn in self.mode_buttons.items():
            if mode == self.current_mode:
                btn.config(bg=self.get_mode_color(), fg="white")
            else:
                btn.config(bg=self.colors["card"], fg=self.colors["text_dim"])
                
    def update_stats(self):
        self.pomodoro_count_label.config(text=f"🍅 {self.completed_pomodoros} 个番茄")
        focus_mins = self.total_focus_seconds // 60
        self.focus_time_label.config(text=f"⏱ {focus_mins} 分钟专注")
        
        cycle_pos = self.completed_pomodoros % self.settings["cycles_before_long"]
        for i, indicator in enumerate(self.cycle_indicators):
            if i < cycle_pos:
                indicator.config(text="●", fg=self.colors["work"])
            else:
                indicator.config(text="○", fg=self.colors["border"])
                
    def switch_mode(self, mode, duration):
        self.pause_timer()
        self.current_mode = mode
        self.time_left = duration * 60
        self.update_mode_buttons()
        self.update_display()
        
    def toggle_timer(self):
        if self.is_running:
            self.pause_timer()
        else:
            self.start_timer()
            
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.session_start = datetime.now()
            self.run_timer()
            
    def run_timer(self):
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            if self.current_mode == "work":
                self.total_focus_seconds += 1
            self.update_display()
            self.root.after(1000, self.run_timer)
        elif self.time_left == 0:
            self.on_timer_complete()
            
    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = True
            
    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.time_left = self.get_mode_duration() * 60
        self.update_display()
        
    def on_timer_complete(self):
        self.is_running = False
        
        if self.current_mode == "work":
            self.completed_pomodoros += 1
            self.save_pomodoro_record()
            
            if self.settings["sound_enabled"]:
                try:
                    import winsound
                    winsound.MessageBeep()
                except:
                    pass
                    
            if self.completed_pomodoros % self.settings["cycles_before_long"] == 0:
                self.switch_mode("long_break", self.settings["long_break"])
                messagebox.showinfo(
                    "🎉 太棒了！",
                    f"完成第 {self.completed_pomodoros} 个番茄！\n休息一下吧~"
                )
            else:
                self.switch_mode("short_break", self.settings["short_break"])
                messagebox.showinfo(
                    "⏰ 专注完成",
                    f"完成第 {self.completed_pomodoros} 个番茄！\n休息 {self.settings['short_break']} 分钟"
                )
                
            if self.settings["auto_start_break"]:
                self.start_timer()
        else:
            self.switch_mode("work", self.settings["work_duration"])
            messagebox.showinfo("☕ 休息结束", "准备好开始新的专注了吗？")
            
            if self.settings["auto_start_work"]:
                self.start_timer()
                
        self.quote_label.config(text=random.choice(self.quotes))
        self.save_data()
        
    def on_task_select(self, event):
        selection = self.task_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.tasks):
                self.current_task = self.tasks[idx]["name"]
                self.current_task_label.config(text=self.current_task, fg=self.colors["text"])
                
    def add_task(self):
        task_name = simpledialog.askstring("添加任务", "输入任务名称:", parent=self.root)
        if task_name and task_name.strip():
            self.tasks.append({
                "name": task_name.strip(),
                "completed": False,
                "pomodoros": 0
            })
            self.refresh_task_list()
            self.save_data()
            
    def complete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.tasks):
                self.tasks[idx]["completed"] = not self.tasks[idx]["completed"]
                self.refresh_task_list()
                self.save_data()
                
    def delete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.tasks):
                if self.current_task == self.tasks[idx]["name"]:
                    self.current_task = None
                    self.current_task_label.config(text="点击下方选择任务", fg=self.colors["text_dim"])
                del self.tasks[idx]
                self.refresh_task_list()
                self.save_data()
                
    def refresh_task_list(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.tasks:
            status = "✓" if task["completed"] else "○"
            pomos = f" ({task.get('pomodoros', 0)}🍅)" if task.get("pomodoros", 0) > 0 else ""
            self.task_listbox.insert(tk.END, f"{status} {task['name']}{pomos}")
            
    def save_pomodoro_record(self):
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "task": self.current_task,
            "duration": self.settings["work_duration"]
        })
        
        if self.current_task:
            for task in self.tasks:
                if task["name"] == self.current_task:
                    task["pomodoros"] = task.get("pomodoros", 0) + 1
                    break
        self.refresh_task_list()
        
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("320x380")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        win.configure(bg=self.colors["bg"])
        
        tk.Label(
            win,
            text="⚙ 设置",
            font=("Microsoft YaHei", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        ).pack(pady=15)
        
        time_frame = tk.LabelFrame(
            win,
            text="时间设置 (分钟)",
            font=("Microsoft YaHei", 10),
            bg=self.colors["card"],
            fg=self.colors["text"],
            padx=15,
            pady=10
        )
        time_frame.pack(fill="x", padx=20, pady=5)
        
        work_var = tk.StringVar(value=str(self.settings["work_duration"]))
        short_var = tk.StringVar(value=str(self.settings["short_break"]))
        long_var = tk.StringVar(value=str(self.settings["long_break"]))
        
        for i, (label, var) in enumerate([
            ("专注时间:", work_var),
            ("短休息:", short_var),
            ("长休息:", long_var)
        ]):
            row = tk.Frame(time_frame, bg=self.colors["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=self.colors["card"], fg=self.colors["text"]).pack(side="left")
            tk.Entry(row, textvariable=var, width=8, font=("Consolas", 10)).pack(side="right")
            
        option_frame = tk.LabelFrame(
            win,
            text="选项",
            font=("Microsoft YaHei", 10),
            bg=self.colors["card"],
            fg=self.colors["text"],
            padx=15,
            pady=10
        )
        option_frame.pack(fill="x", padx=20, pady=5)
        
        sound_var = tk.BooleanVar(value=self.settings["sound_enabled"])
        auto_break_var = tk.BooleanVar(value=self.settings["auto_start_break"])
        auto_work_var = tk.BooleanVar(value=self.settings["auto_start_work"])
        
        for text, var in [
            ("启用提示音", sound_var),
            ("休息自动开始", auto_break_var),
            ("专注自动开始", auto_work_var)
        ]:
            tk.Checkbutton(
                option_frame,
                text=text,
                variable=var,
                bg=self.colors["card"],
                fg=self.colors["text"],
                selectcolor=self.colors["bg"],
                activebackground=self.colors["card"],
                activeforeground=self.colors["text"]
            ).pack(anchor="w", pady=2)
            
        def save():
            try:
                self.settings["work_duration"] = int(work_var.get())
                self.settings["short_break"] = int(short_var.get())
                self.settings["long_break"] = int(long_var.get())
                self.settings["sound_enabled"] = sound_var.get()
                self.settings["auto_start_break"] = auto_break_var.get()
                self.settings["auto_start_work"] = auto_work_var.get()
                
                if not self.is_running:
                    self.time_left = self.get_mode_duration() * 60
                    self.update_display()
                    
                self.save_data()
                win.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
                
        save_btn = tk.Label(
            win,
            text="保存设置",
            font=("Microsoft YaHei", 10),
            bg=self.colors["accent"],
            fg="white",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        save_btn.pack(pady=20)
        save_btn.bind("<Button-1>", lambda e: save())
        
    def load_data(self):
        try:
            if os.path.exists("pomodoro_data.json"):
                with open("pomodoro_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                self.settings.update(data.get("settings", {}))
                self.tasks = data.get("tasks", [])
                self.history = data.get("history", [])
                
                today = datetime.now().strftime("%Y-%m-%d")
                if data.get("date") == today:
                    self.completed_pomodoros = data.get("completed_pomodoros", 0)
                    self.total_focus_seconds = data.get("total_focus_seconds", 0)
                    self.current_task = data.get("current_task")
                    if self.current_task:
                        self.current_task_label.config(text=self.current_task, fg=self.colors["text"])
                        
                self.time_left = self.get_mode_duration() * 60
        except Exception as e:
            print(f"加载数据失败: {e}")
            
    def save_data(self):
        data = {
            "settings": self.settings,
            "tasks": self.tasks,
            "history": self.history,
            "completed_pomodoros": self.completed_pomodoros,
            "total_focus_seconds": self.total_focus_seconds,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "current_task": self.current_task
        }
        try:
            with open("pomodoro_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")


def main():
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()


if __name__ == "__main__":
    main()