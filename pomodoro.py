import tkinter as tk
from tkinter import ttk, messagebox
import math
import json
import os
from datetime import datetime
import winsound

class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍅 番茄钟计时器")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        
        self.work_time = 25 * 60
        self.short_break = 5 * 60
        self.long_break = 15 * 60
        self.cycles_before_long = 4
        
        self.current_time = self.work_time
        self.is_running = False
        self.is_paused = False
        self.current_mode = "work"
        self.completed_cycles = 0
        self.current_task = None
        self.tasks = []
        
        self.load_data()
        self.setup_ui()
        self.update_timer_display()
        
    def setup_ui(self):
        self.root.configure(bg="#f5f5f5")
        
        title_label = tk.Label(
            self.root, 
            text="🍅 番茄钟计时器", 
            font=("Microsoft YaHei", 20, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        title_label.pack(pady=15)
        
        self.mode_label = tk.Label(
            self.root,
            text="工作时间",
            font=("Microsoft YaHei", 14),
            bg="#f5f5f5",
            fg="#666"
        )
        self.mode_label.pack()
        
        self.canvas_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.canvas_frame.pack(pady=10)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            width=200, 
            height=200, 
            bg="#f5f5f5",
            highlightthickness=0
        )
        self.canvas.pack()
        
        self.draw_timer()
        
        self.time_label = tk.Label(
            self.root,
            text="25:00",
            font=("Microsoft YaHei", 48, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        self.time_label.place(relx=0.5, rely=0.35, anchor="center")
        
        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.pack(pady=15)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ 开始",
            font=("Microsoft YaHei", 12),
            width=8,
            bg="#4CAF50",
            fg="white",
            relief="flat",
            command=self.start_timer
        )
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.pause_btn = tk.Button(
            btn_frame,
            text="⏸ 暂停",
            font=("Microsoft YaHei", 12),
            width=8,
            bg="#FF9800",
            fg="white",
            relief="flat",
            command=self.pause_timer,
            state="disabled"
        )
        self.pause_btn.grid(row=0, column=1, padx=5)
        
        self.reset_btn = tk.Button(
            btn_frame,
            text="⏹ 重置",
            font=("Microsoft YaHei", 12),
            width=8,
            bg="#f44336",
            fg="white",
            relief="flat",
            command=self.reset_timer
        )
        self.reset_btn.grid(row=0, column=2, padx=5)
        
        task_frame = tk.LabelFrame(
            self.root,
            text="📝 任务列表",
            font=("Microsoft YaHei", 12),
            bg="#f5f5f5",
            fg="#333",
            padx=10,
            pady=5
        )
        task_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.task_listbox = tk.Listbox(
            task_frame,
            font=("Microsoft YaHei", 11),
            height=6,
            bg="white",
            relief="flat",
            selectbackground="#4CAF50"
        )
        self.task_listbox.pack(fill="both", expand=True, pady=5)
        self.task_listbox.bind('<Double-Button-1>', self.select_task)
        
        task_btn_frame = tk.Frame(task_frame, bg="#f5f5f5")
        task_btn_frame.pack(fill="x")
        
        tk.Button(
            task_btn_frame,
            text="+ 添加",
            font=("Microsoft YaHei", 10),
            width=8,
            bg="#2196F3",
            fg="white",
            relief="flat",
            command=self.add_task
        ).pack(side="left", padx=2)
        
        tk.Button(
            task_btn_frame,
            text="✓ 完成",
            font=("Microsoft YaHei", 10),
            width=8,
            bg="#4CAF50",
            fg="white",
            relief="flat",
            command=self.complete_task
        ).pack(side="left", padx=2)
        
        tk.Button(
            task_btn_frame,
            text="✕ 删除",
            font=("Microsoft YaHei", 10),
            width=8,
            bg="#f44336",
            fg="white",
            relief="flat",
            command=self.delete_task
        ).pack(side="left", padx=2)
        
        self.current_task_label = tk.Label(
            self.root,
            text="当前任务: 无",
            font=("Microsoft YaHei", 11),
            bg="#f5f5f5",
            fg="#666"
        )
        self.current_task_label.pack(pady=5)
        
        stats_frame = tk.Frame(self.root, bg="#e8f5e9")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.today_label = tk.Label(
            stats_frame,
            text="今日: 0 个番茄",
            font=("Microsoft YaHei", 11),
            bg="#e8f5e9",
            fg="#2E7D32"
        )
        self.today_label.pack(side="left", padx=20, pady=10)
        
        self.cycle_label = tk.Label(
            stats_frame,
            text="周期: 0/4",
            font=("Microsoft YaHei", 11),
            bg="#e8f5e9",
            fg="#2E7D32"
        )
        self.cycle_label.pack(side="right", padx=20, pady=10)
        
        self.update_task_listbox()
        self.update_stats()
        
    def draw_timer(self):
        self.canvas.delete("all")
        
        center_x = 100
        center_y = 100
        radius = 80
        
        total_time = self.get_current_total_time()
        progress = (total_time - self.current_time) / total_time
        
        if self.current_mode == "work":
            color = "#4CAF50"
        elif self.current_mode == "short_break":
            color = "#2196F3"
        else:
            color = "#9C27B0"
        
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="#ddd", width=8
        )
        
        if progress > 0:
            start_angle = 90
            extent = -progress * 360
            self.canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=extent,
                outline=color, width=8, style="arc"
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
        
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.run_timer()
        
    def run_timer(self):
        if self.is_running and self.current_time > 0:
            self.current_time -= 1
            self.update_timer_display()
            self.root.after(1000, self.run_timer)
        elif self.current_time == 0:
            self.timer_finished()
            
    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = True
            self.start_btn.config(state="normal", text="▶ 继续")
            self.pause_btn.config(state="disabled")
            
    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.current_time = self.get_current_total_time()
        self.update_timer_display()
        self.start_btn.config(state="normal", text="▶ 开始")
        self.pause_btn.config(state="disabled")
        
    def timer_finished(self):
        self.is_running = False
        
        if self.current_mode == "work":
            self.completed_cycles += 1
            self.save_completed_pomodoro()
            
            winsound.MessageBeep(winsound.MB_OK)
            
            if self.completed_cycles % self.cycles_before_long == 0:
                self.current_mode = "long_break"
                self.current_time = self.long_break
                messagebox.showinfo("提示", "🎉 完成一个周期！现在是长休息时间 (15分钟)")
            else:
                self.current_mode = "short_break"
                self.current_time = self.short_break
                messagebox.showinfo("提示", "⏰ 工作时间结束！休息一下吧 (5分钟)")
        else:
            self.current_mode = "work"
            self.current_time = self.work_time
            messagebox.showinfo("提示", "☕ 休息结束！开始新的番茄钟")
        
        self.update_mode_label()
        self.update_timer_display()
        self.update_stats()
        
        self.start_btn.config(state="normal", text="▶ 开始")
        self.pause_btn.config(state="disabled")
        
    def update_mode_label(self):
        if self.current_mode == "work":
            self.mode_label.config(text="工作时间", fg="#4CAF50")
        elif self.current_mode == "short_break":
            self.mode_label.config(text="短休息", fg="#2196F3")
        else:
            self.mode_label.config(text="长休息", fg="#9C27B0")
            
    def add_task(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加任务")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="任务名称:", font=("Microsoft YaHei", 11)).pack(pady=5)
        
        task_entry = tk.Entry(dialog, font=("Microsoft YaHei", 11), width=30)
        task_entry.pack(pady=5)
        
        def confirm():
            task = task_entry.get().strip()
            if task:
                self.tasks.append({"name": task, "completed": False})
                self.update_task_listbox()
                self.save_data()
                dialog.destroy()
                
        tk.Button(
            dialog, 
            text="添加", 
            font=("Microsoft YaHei", 10),
            bg="#4CAF50", fg="white", relief="flat",
            command=confirm
        ).pack(pady=5)
        
        task_entry.focus()
        dialog.bind('<Return>', lambda e: confirm())
        
    def select_task(self, event):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_task = self.tasks[index]["name"]
            self.current_task_label.config(text=f"当前任务: {self.current_task}")
            
    def complete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            self.tasks[index]["completed"] = True
            self.update_task_listbox()
            self.save_data()
            
    def delete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            index = selection[0]
            del self.tasks[index]
            if self.current_task == self.tasks[index]["name"] if index < len(self.tasks) else True:
                self.current_task = None
                self.current_task_label.config(text="当前任务: 无")
            self.update_task_listbox()
            self.save_data()
            
    def update_task_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.tasks:
            status = "✓" if task["completed"] else "○"
            self.task_listbox.insert(tk.END, f"{status} {task['name']}")
            
    def load_data(self):
        try:
            if os.path.exists("pomodoro_data.json"):
                with open("pomodoro_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    today = datetime.now().strftime("%Y-%m-%d")
                    if data.get("date") == today:
                        self.completed_cycles = data.get("completed_cycles", 0)
        except:
            self.tasks = []
            self.completed_cycles = 0
            
    def save_data(self):
        data = {
            "tasks": self.tasks,
            "completed_cycles": self.completed_cycles,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        with open("pomodoro_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def save_completed_pomodoro(self):
        self.save_data()
        
    def update_stats(self):
        self.today_label.config(text=f"今日: {self.completed_cycles} 个番茄")
        cycle_in_period = self.completed_cycles % self.cycles_before_long
        self.cycle_label.config(text=f"周期: {cycle_in_period}/{self.cycles_before_long}")
        
def main():
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
