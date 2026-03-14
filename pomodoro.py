import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta
from threading import Thread
import winsound
import random

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command=None, bg_color="#4CAF50", fg_color="white", width=100, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.radius = 8
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        self.draw_button(bg_color)
        
    def draw_button(self, color):
        self.delete("all")
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, self.radius, fill=color, outline="")
        self.create_text(self.width//2, self.height//2, text=self.text, fill=self.fg_color, font=("Microsoft YaHei", 11, "bold"))
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def on_enter(self, event):
        self.draw_button(self.adjust_color(self.bg_color, 20))
        self.config(cursor="hand2")
        
    def on_leave(self, event):
        self.draw_button(self.bg_color)
        self.config(cursor="")
        
    def on_click(self, event):
        self.draw_button(self.adjust_color(self.bg_color, -20))
        
    def on_release(self, event):
        self.draw_button(self.adjust_color(self.bg_color, 20))
        if self.command:
            self.command()
            
    def adjust_color(self, hex_color, amount):
        r = max(0, min(255, int(hex_color[1:3], 16) + amount))
        g = max(0, min(255, int(hex_color[3:5], 16) + amount))
        b = max(0, min(255, int(hex_color[5:7], 16) + amount))
        return f"#{r:02x}{g:02x}{b:02x}"

class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍅 番茄专注")
        self.root.geometry("500x750")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        
        # 默认设置
        self.work_time = 25 * 60
        self.short_break = 5 * 60
        self.long_break = 15 * 60
        self.cycles_before_long = 4
        self.sound_enabled = True
        self.auto_start_break = False
        self.auto_start_work = False
        
        # 状态
        self.current_time = self.work_time
        self.is_running = False
        self.is_paused = False
        self.current_mode = "work"
        self.completed_cycles = 0
        self.current_task = None
        self.tasks = []
        self.history = []
        self.total_focus_time = 0
        
        # 语录
        self.quotes = [
            "专注当下，成就未来",
            "千里之行，始于足下",
            "保持专注，保持高效",
            "每一个番茄都是进步",
            "专注是一种力量",
            "今天也是充满能量的一天",
            "小步快跑，持续进步",
            "专注让你与众不同"
        ]
        
        self.load_data()
        self.setup_ui()
        self.update_timer_display()
        
    def setup_ui(self):
        # 顶部标题栏
        header_frame = tk.Frame(self.root, bg="#16213e", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🍅 番茄专注",
            font=("Microsoft YaHei", 18, "bold"),
            bg="#16213e",
            fg="#e94560"
        ).pack(side="left", padx=20, pady=10)
        
        # 设置按钮
        settings_btn = tk.Label(header_frame, text="⚙", font=("Microsoft YaHei", 16), bg="#16213e", fg="#fff")
        settings_btn.pack(side="right", padx=20, pady=10)
        settings_btn.bind("<Button-1>", lambda e: self.open_settings())
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(cursor="hand2", fg="#e94560"))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(cursor="", fg="#fff"))
        
        # 主内容区
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 模式标签
        self.mode_label = tk.Label(
            main_frame,
            text="专注时间",
            font=("Microsoft YaHei", 14),
            bg="#1a1a2e",
            fg="#e94560"
        )
        self.mode_label.pack()
        
        # 计时器圆形显示
        timer_frame = tk.Frame(main_frame, bg="#1a1a2e")
        timer_frame.pack(pady=20)
        
        self.canvas = tk.Canvas(
            timer_frame,
            width=240,
            height=240,
            bg="#1a1a2e",
            highlightthickness=0
        )
        self.canvas.pack()
        
        # 时间显示
        self.time_label = tk.Label(
            main_frame,
            text="25:00",
            font=("Microsoft YaHei", 56, "bold"),
            bg="#1a1a2e",
            fg="#fff"
        )
        self.time_label.place(relx=0.5, rely=0.22, anchor="center")
        
        # 语录
        self.quote_label = tk.Label(
            main_frame,
            text=random.choice(self.quotes),
            font=("Microsoft YaHei", 11, "italic"),
            bg="#1a1a2e",
            fg="#888",
            wraplength=400
        )
        self.quote_label.pack(pady=(180, 20))
        
        # 控制按钮
        btn_frame = tk.Frame(main_frame, bg="#1a1a2e")
        btn_frame.pack(pady=10)
        
        self.start_btn = ModernButton(btn_frame, "▶ 开始", self.start_timer, "#0f3460", width=100, height=42)
        self.start_btn.grid(row=0, column=0, padx=8)
        
        self.pause_btn = ModernButton(btn_frame, "⏸ 暂停", self.pause_timer, "#e94560", width=100, height=42)
        self.pause_btn.grid(row=0, column=1, padx=8)
        
        self.reset_btn = ModernButton(btn_frame, "⏹ 重置", self.reset_timer, "#533483", width=100, height=42)
        self.reset_btn.grid(row=0, column=2, padx=8)
        
        # 快捷时间按钮
        quick_frame = tk.Frame(main_frame, bg="#1a1a2e")
        quick_frame.pack(pady=15)
        
        for i, (text, mode, time_val) in enumerate([
            ("🍅 专注", "work", self.work_time),
            ("☕ 短休", "short_break", self.short_break),
            ("🛋 长休", "long_break", self.long_break)
        ]):
            btn = tk.Label(quick_frame, text=text, font=("Microsoft YaHei", 10), bg="#16213e", fg="#fff", padx=12, pady=6)
            btn.grid(row=0, column=i, padx=5)
            btn.bind("<Button-1>", lambda e, m=mode, t=time_val: self.switch_mode(m, t))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#0f3460", cursor="hand2"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#16213e"))
        
        # 当前任务
        task_section = tk.Frame(main_frame, bg="#16213e", padx=15, pady=15)
        task_section.pack(fill="x", pady=10)
        
        tk.Label(task_section, text="📝 当前任务", font=("Microsoft YaHei", 12, "bold"), bg="#16213e", fg="#fff").pack(anchor="w")
        
        self.current_task_label = tk.Label(
            task_section,
            text="点击选择或添加任务",
            font=("Microsoft YaHei", 11),
            bg="#16213e",
            fg="#888"
        )
        self.current_task_label.pack(anchor="w", pady=(5, 0))
        
        # 任务列表
        task_list_frame = tk.Frame(task_section, bg="#16213e")
        task_list_frame.pack(fill="x", pady=(10, 0))
        
        self.task_var = tk.StringVar(value=[])
        self.task_listbox = tk.Listbox(
            task_list_frame,
            font=("Microsoft YaHei", 10),
            height=4,
            bg="#1a1a2e",
            fg="#fff",
            relief="flat",
            selectbackground="#e94560",
            selectforeground="#fff",
            highlightthickness=0,
            listvariable=self.task_var
        )
        self.task_listbox.pack(side="left", fill="both", expand=True)
        self.task_listbox.bind('<<ListboxSelect>>', self.on_task_select)
        self.task_listbox.bind('<Double-Button-1>', self.on_task_double_click)
        
        scrollbar = tk.Scrollbar(task_list_frame, bg="#1a1a2e", troughcolor="#16213e")
        scrollbar.pack(side="right", fill="y")
        self.task_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.task_listbox.yview)
        
        # 任务操作按钮
        task_btn_frame = tk.Frame(task_section, bg="#16213e")
        task_btn_frame.pack(fill="x", pady=(10, 0))
        
        for text, cmd, color in [
            ("+ 添加", self.add_task, "#0f3460"),
            ("✓ 完成", self.complete_task, "#4CAF50"),
            ("✕ 删除", self.delete_task, "#f44336")
        ]:
            btn = tk.Label(task_btn_frame, text=text, font=("Microsoft YaHei", 9), bg=color, fg="#fff", padx=10, pady=4)
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.lighten_color(b.winfo_rgb(b.cget("bg")))))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
        
        # 统计信息
        stats_frame = tk.Frame(main_frame, bg="#0f3460", padx=15, pady=12)
        stats_frame.pack(fill="x", pady=10)
        
        self.today_label = tk.Label(stats_frame, text="今日: 0 个番茄", font=("Microsoft YaHei", 11), bg="#0f3460", fg="#fff")
        self.today_label.pack(side="left")
        
        self.focus_time_label = tk.Label(stats_frame, text="专注: 0 分钟", font=("Microsoft YaHei", 11), bg="#0f3460", fg="#fff")
        self.focus_time_label.pack(side="right")
        
        # 周期指示器
        self.cycle_indicators = []
        cycle_frame = tk.Frame(main_frame, bg="#1a1a2e")
        cycle_frame.pack(pady=5)
        
        tk.Label(cycle_frame, text="当前周期: ", font=("Microsoft YaHei", 10), bg="#1a1a2e", fg="#888").pack(side="left")
        
        for i in range(4):
            indicator = tk.Label(cycle_frame, text="○", font=("Microsoft YaHei", 12), bg="#1a1a2e", fg="#444")
            indicator.pack(side="left", padx=3)
            self.cycle_indicators.append(indicator)
        
        self.update_task_listbox()
        self.update_stats()
        self.draw_timer()
        
        # 键盘快捷键
        self.root.bind('<space>', lambda e: self.toggle_timer())
        self.root.bind('<r>', lambda e: self.reset_timer())
        self.root.bind('<Escape>', lambda e: self.pause_timer())
        
    def lighten_color(self, rgb_tuple):
        r, g, b = rgb_tuple
        r = min(65535, int(r * 1.2))
        g = min(65535, int(g * 1.2))
        b = min(65535, int(b * 1.2))
        return f"#{r//256:02x}{g//256:02x}{b//256:02x}"
        
    def draw_timer(self):
        self.canvas.delete("all")
        
        center_x = 120
        center_y = 120
        radius = 100
        
        total_time = self.get_current_total_time()
        progress = (total_time - self.current_time) / total_time if total_time > 0 else 0
        
        colors = {
            "work": ("#e94560", "#ff6b6b"),
            "short_break": ("#4ecca3", "#6effd1"),
            "long_break": ("#533483", "#7b52ab")
        }
        primary_color, glow_color = colors.get(self.current_mode, ("#e94560", "#ff6b6b"))
        
        # 外圈发光效果
        for i in range(3):
            self.canvas.create_oval(
                center_x - radius - 5 - i*2, center_y - radius - 5 - i*2,
                center_x + radius + 5 + i*2, center_y + radius + 5 + i*2,
                outline=glow_color, width=1, stipple="gray50"
            )
        
        # 背景圆环
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="#0f3460", width=8
        )
        
        # 进度圆环
        if progress > 0:
            start_angle = 90
            extent = -progress * 360
            
            # 创建渐变效果
            self.canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=extent,
                outline=primary_color, width=8, style="arc"
            )
        
        # 中心装饰
        self.canvas.create_oval(
            center_x - 8, center_y - 8,
            center_x + 8, center_y + 8,
            fill=primary_color, outline=""
        )
        
    def get_current_total_time(self):
        if self.current_mode == "work":
            return self.work_time
        elif self.current_mode == "short_break":
            return self.short_break
        else:
            return self.long_break
        
    def update_timer_display(self):
        minutes = self.current_time // 60
        seconds = self.current_time % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        self.draw_timer()
        
    def switch_mode(self, mode, time_val):
        self.pause_timer()
        self.current_mode = mode
        self.current_time = time_val
        self.update_mode_label()
        self.update_timer_display()
        
    def update_mode_label(self):
        mode_names = {
            "work": "专注时间",
            "short_break": "短休息",
            "long_break": "长休息"
        }
        mode_colors = {
            "work": "#e94560",
            "short_break": "#4ecca3",
            "long_break": "#533483"
        }
        self.mode_label.config(text=mode_names.get(self.current_mode, "专注时间"), fg=mode_colors.get(self.current_mode, "#e94560"))
        
    def toggle_timer(self):
        if self.is_running:
            self.pause_timer()
        else:
            self.start_timer()
            
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.run_timer()
            
    def run_timer(self):
        if self.is_running and self.current_time > 0:
            self.current_time -= 1
            if self.current_mode == "work":
                self.total_focus_time += 1
            self.update_timer_display()
            self.root.after(1000, self.run_timer)
        elif self.current_time == 0:
            self.timer_finished()
            
    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = True
            
    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.current_time = self.get_current_total_time()
        self.update_timer_display()
        
    def timer_finished(self):
        self.is_running = False
        
        if self.current_mode == "work":
            self.completed_cycles += 1
            self.save_completed_pomodoro()
            
            if self.sound_enabled:
                winsound.MessageBeep(winsound.MB_OK)
            
            if self.completed_cycles % self.cycles_before_long == 0:
                self.current_mode = "long_break"
                self.current_time = self.long_break
                messagebox.showinfo("🎉 恭喜！", f"完成第 {self.completed_cycles} 个番茄！\n\n休息一下吧，你做得很好！")
            else:
                self.current_mode = "short_break"
                self.current_time = self.short_break
                messagebox.showinfo("⏰ 专注完成", f"完成第 {self.completed_cycles} 个番茄！\n\n休息 {self.short_break//60} 分钟")
                
            if self.auto_start_break:
                self.start_timer()
        else:
            self.current_mode = "work"
            self.current_time = self.work_time
            messagebox.showinfo("☕ 休息结束", "准备好开始新的专注了吗？")
            
            if self.auto_start_work:
                self.start_timer()
        
        self.quote_label.config(text=random.choice(self.quotes))
        self.update_mode_label()
        self.update_timer_display()
        self.update_stats()
        
    def on_task_select(self, event):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.tasks):
                self.current_task = self.tasks[index]["name"]
                self.current_task_label.config(text=self.current_task, fg="#fff")
                
    def on_task_double_click(self, event):
        self.on_task_select(event)
        
    def add_task(self):
        task = simpledialog.askstring("添加任务", "请输入任务名称:", parent=self.root)
        if task and task.strip():
            self.tasks.append({"name": task.strip(), "completed": False, "pomodoros": 0})
            self.update_task_listbox()
            self.save_data()
            
    def complete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.tasks):
                self.tasks[index]["completed"] = not self.tasks[index]["completed"]
                self.update_task_listbox()
                self.save_data()
                
    def delete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.tasks):
                if self.current_task == self.tasks[index]["name"]:
                    self.current_task = None
                    self.current_task_label.config(text="点击选择或添加任务", fg="#888")
                del self.tasks[index]
                self.update_task_listbox()
                self.save_data()
                
    def update_task_listbox(self):
        task_names = []
        for task in self.tasks:
            status = "✓" if task["completed"] else "○"
            pomos = f" ({task.get('pomodoros', 0)}🍅)" if task.get('pomodoros', 0) > 0 else ""
            task_names.append(f"{status} {task['name']}{pomos}")
        self.task_var.set(task_names)
        
    def update_stats(self):
        self.today_label.config(text=f"今日: {self.completed_cycles} 个番茄")
        focus_mins = self.total_focus_time // 60
        self.focus_time_label.config(text=f"专注: {focus_mins} 分钟")
        
        # 更新周期指示器
        cycle_in_period = self.completed_cycles % self.cycles_before_long
        for i, indicator in enumerate(self.cycle_indicators):
            if i < cycle_in_period:
                indicator.config(text="●", fg="#e94560")
            else:
                indicator.config(text="○", fg="#444")
                
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("350x400")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.configure(bg="#1a1a2e")
        
        tk.Label(settings_window, text="⚙ 设置", font=("Microsoft YaHei", 16, "bold"), bg="#1a1a2e", fg="#fff").pack(pady=15)
        
        # 时间设置
        time_frame = tk.LabelFrame(settings_window, text="时间设置 (分钟)", font=("Microsoft YaHei", 10), bg="#16213e", fg="#fff", padx=15, pady=10)
        time_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(time_frame, text="专注时间:", bg="#16213e", fg="#fff").grid(row=0, column=0, sticky="w", pady=5)
        work_spin = tk.Spinbox(time_frame, from_=1, to=60, width=8, font=("Microsoft YaHei", 10))
        work_spin.delete(0, "end")
        work_spin.insert(0, str(self.work_time // 60))
        work_spin.grid(row=0, column=1, padx=10)
        
        tk.Label(time_frame, text="短休息:", bg="#16213e", fg="#fff").grid(row=1, column=0, sticky="w", pady=5)
        short_spin = tk.Spinbox(time_frame, from_=1, to=30, width=8, font=("Microsoft YaHei", 10))
        short_spin.delete(0, "end")
        short_spin.insert(0, str(self.short_break // 60))
        short_spin.grid(row=1, column=1, padx=10)
        
        tk.Label(time_frame, text="长休息:", bg="#16213e", fg="#fff").grid(row=2, column=0, sticky="w", pady=5)
        long_spin = tk.Spinbox(time_frame, from_=1, to=60, width=8, font=("Microsoft YaHei", 10))
        long_spin.delete(0, "end")
        long_spin.insert(0, str(self.long_break // 60))
        long_spin.grid(row=2, column=1, padx=10)
        
        # 选项设置
        option_frame = tk.LabelFrame(settings_window, text="选项", font=("Microsoft YaHei", 10), bg="#16213e", fg="#fff", padx=15, pady=10)
        option_frame.pack(fill="x", padx=20, pady=5)
        
        sound_var = tk.BooleanVar(value=self.sound_enabled)
        tk.Checkbutton(option_frame, text="启用提示音", variable=sound_var, bg="#16213e", fg="#fff", selectcolor="#1a1a2e", activebackground="#16213e", activeforeground="#fff").pack(anchor="w", pady=3)
        
        auto_break_var = tk.BooleanVar(value=self.auto_start_break)
        tk.Checkbutton(option_frame, text="休息自动开始", variable=auto_break_var, bg="#16213e", fg="#fff", selectcolor="#1a1a2e", activebackground="#16213e", activeforeground="#fff").pack(anchor="w", pady=3)
        
        auto_work_var = tk.BooleanVar(value=self.auto_start_work)
        tk.Checkbutton(option_frame, text="专注自动开始", variable=auto_work_var, bg="#16213e", fg="#fff", selectcolor="#1a1a2e", activebackground="#16213e", activeforeground="#fff").pack(anchor="w", pady=3)
        
        def save_settings():
            self.work_time = int(work_spin.get()) * 60
            self.short_break = int(short_spin.get()) * 60
            self.long_break = int(long_spin.get()) * 60
            self.sound_enabled = sound_var.get()
            self.auto_start_break = auto_break_var.get()
            self.auto_start_work = auto_work_var.get()
            
            if not self.is_running:
                self.current_time = self.get_current_total_time()
                self.update_timer_display()
            
            self.save_data()
            settings_window.destroy()
            
        ModernButton(settings_window, "保存设置", save_settings, "#4CAF50", width=120, height=40).pack(pady=20)
        
    def load_data(self):
        try:
            if os.path.exists("pomodoro_data.json"):
                with open("pomodoro_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.history = data.get("history", [])
                    self.sound_enabled = data.get("sound_enabled", True)
                    self.auto_start_break = data.get("auto_start_break", False)
                    self.auto_start_work = data.get("auto_start_work", False)
                    self.work_time = data.get("work_time", 25) * 60
                    self.short_break = data.get("short_break", 5) * 60
                    self.long_break = data.get("long_break", 15) * 60
                    
                    today = datetime.now().strftime("%Y-%m-%d")
                    if data.get("date") == today:
                        self.completed_cycles = data.get("completed_cycles", 0)
                        self.total_focus_time = data.get("total_focus_time", 0)
                        self.current_task = data.get("current_task")
        except Exception as e:
            print(f"加载数据失败: {e}")
            self.tasks = []
            self.history = []
            
    def save_data(self):
        data = {
            "tasks": self.tasks,
            "history": self.history,
            "completed_cycles": self.completed_cycles,
            "total_focus_time": self.total_focus_time,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "current_task": self.current_task,
            "sound_enabled": self.sound_enabled,
            "auto_start_break": self.auto_start_break,
            "auto_start_work": self.auto_start_work,
            "work_time": self.work_time // 60,
            "short_break": self.short_break // 60,
            "long_break": self.long_break // 60
        }
        try:
            with open("pomodoro_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
            
    def save_completed_pomodoro(self):
        # 记录历史
        now = datetime.now()
        self.history.append({
            "timestamp": now.isoformat(),
            "task": self.current_task,
            "duration": self.work_time // 60
        })
        
        # 更新任务的番茄数
        if self.current_task:
            for task in self.tasks:
                if task["name"] == self.current_task:
                    task["pomodoros"] = task.get("pomodoros", 0) + 1
                    break
                    
        self.save_data()
        
def main():
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
