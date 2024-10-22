import uuid
import os
import time
import json
from datetime import datetime, date, timedelta
from collections import Counter
from textwrap import wrap
import pygame
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.padding import Padding
from rich.align import Align
from rich.style import Style

class TaskManager:
    def __init__(self, file_path='tasks.json'):
        self.file_path = file_path
        self.tasks = {}
        self.user_stats = {}
        self.load_data()
        self.clean_old_tasks()
        
        # Pomodoro timer attributes
        self.timer_start = None
        self.timer_end = None
        self.timer_type = None
        self.timer_paused = False
        self.timer_pause_start = None
        self.focus_duration = 30  # Default focus time: 30 minutes
        self.short_break_duration = 10  # Default short break: 10 minutes
        self.long_break_duration = 15  # Default long break: 15 minutes
        self.current_phase = 'focus'
        self.pomodoro_count = 0
        self.max_pomodoros = 4
        self.total_completed_pomodoros = 0  # New attribute to track total completed pomodoros
        self.last_pomodoro_date = date.today()  # New attribute to track the date of the last pomodoro

        # Initialize pygame mixer for sound playback
        pygame.mixer.init()
        self.complete_sound = pygame.mixer.Sound(os.path.join('sounds', 'complete.mp3'))
        self.console = Console()

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', {})
                self.user_stats = data.get('user_stats', {})
                
                # Convert date strings back to date objects
                for task in self.tasks.values():
                    task['date'] = datetime.strptime(task['date'], "%Y-%m-%d").date()

    def save_data(self):
        data_to_save = {
            'tasks': {
                task_id: {**task, 'date': task['date'].isoformat()}
                for task_id, task in self.tasks.items()
            },
            'user_stats': self.user_stats
        }
        with open(self.file_path, 'w') as f:
            json.dump(data_to_save, f, indent=2)

    def clean_old_tasks(self):
        today = date.today()
        self.tasks = {
            task_id: task for task_id, task in self.tasks.items()
            if task['date'] == today
        }
        self.save_data()

    def add_task(self, description, user):
        task_id = str(uuid.uuid4())[:8]  # Generate a unique ID
        self.tasks[task_id] = {
            "description": description,
            "completed": False,
            "user": user,
            "date": date.today()
        }
        self.save_data()
        return task_id

    def remove_task(self, task_id, user):
        if task_id in self.tasks and self.tasks[task_id]["user"] == user:
            del self.tasks[task_id]
            self.save_data()
            return True
        return False

    def complete_task(self, task_id, user):
        if task_id in self.tasks and self.tasks[task_id]["user"] == user and not self.tasks[task_id]["completed"]:
            self.tasks[task_id]["completed"] = True
            
            # Update user stats
            if user not in self.user_stats:
                self.user_stats[user] = {"daily": 0, "total": 0}
            self.user_stats[user]["daily"] += 1
            self.user_stats[user]["total"] += 1
            
            self.save_data()
            return True
        return False

    def get_user_tasks(self, user):
        today = date.today()
        return {
            task_id: task for task_id, task in self.tasks.items()
            if task["user"] == user and task["date"] == today and not task["completed"]
        }

    def get_user_stats(self, user):
        return self.user_stats.get(user, {"daily": 0, "total": 0})

    def display_tasks(self):
        while True:
            self.console.clear()
            layout = Layout()
            
            layout.split_column(
                Layout(name="top_padding", size=2),
                Layout(name="main_content")
            )
            
            layout["main_content"].split_column(
                Layout(name="header", size=8),  # Reduced size from default
                Layout(name="body"),
                Layout(name="footer", size=7)  # Adjusted size for footer
            )
            layout["main_content"]["body"].split_row(
                Layout(name="stats", ratio=3),
                Layout(name="tasks", ratio=7)
            )

            # Header
            timer_status = self.get_timer_status()
            layout["main_content"]["header"].update(Panel(
                Align.center(timer_status),
                title="🍅 Pomodoro 🍅",
                border_style="bold",
                padding=(1, 1),
                title_align="center"
            ))

            # Stats
            stats_table = Table(show_header=True, header_style="bold magenta", show_lines=False, box=None, padding=(0, 1))
            stats_table.add_column("User", style="dim", width=22)  # Increased width
            stats_table.add_column("Today", justify="right", width=12)  # Increased width
            stats_table.add_column("All-time", justify="right", width=12)  # Increased width

            daily_stats = {user: stats['daily'] for user, stats in self.user_stats.items() if stats['daily'] > 0}
            total_stats = {user: stats['total'] for user, stats in self.user_stats.items() if stats['total'] > 0}

            for user in set(daily_stats.keys()) | set(total_stats.keys()):
                stats_table.add_row(user, str(daily_stats.get(user, 0)), str(total_stats.get(user, 0)))

            total_completed = sum(stats['total'] for stats in self.user_stats.values())
            stats_panel = Panel(
                stats_table,
                title="User Stats",
                subtitle=f"Total tasks completed (All-time): {total_completed}",  # Updated this line
                border_style="bold green"
            )
            layout["main_content"]["body"]["stats"].update(stats_panel)

            # Tasks
            tasks_table = Table(show_header=True, header_style="bold cyan", show_lines=False, box=None, padding=(0, 1))
            tasks_table.add_column("ID", style="bright_yellow", width=10)  # Changed from "bright_black" to "bright_yellow"
            tasks_table.add_column("Description", style="bright_white", width=60, no_wrap=True)
            tasks_table.add_column("User", style="bright_blue", width=20)

            today = date.today()
            for task_id, task in self.tasks.items():
                if task["date"] == today and not task["completed"]:
                    # Truncate description if it's too long
                    description = task['description'][:57] + "..." if len(task['description']) > 60 else task['description']
                    tasks_table.add_row(
                        task_id,
                        description,
                        task['user']
                    )

            tasks_panel = Panel(
                tasks_table,
                title="Today's Incomplete Tasks",
                border_style="bold cyan",
                title_align="center"
            )
            layout["main_content"]["body"]["tasks"].update(tasks_panel)

            # Footer
            footer_lines = [
                "🎉 Keep up the great work! 🎉",
                "",  # This adds a blank line
                "📝 Use !task command to manage your tasks 📝"
            ]
            footer_text = Text("\n".join(footer_lines), justify="center")
            footer_text.stylize("bold green", 0, len(footer_lines[0]))
            footer_text.stylize("italic cyan", len(footer_lines[0]) + len(footer_lines[1]) + 2, len(footer_text))
            
            # Add padding to move text down and center it horizontally
            # Changed top padding from 2 to 1 to move text up one line
            padded_footer = Align.center(
                Padding(footer_text, (1, 0, 0, 0)),  # 1 line padding at the top (changed from 2)
                vertical="middle"
            )
            
            layout["main_content"]["footer"].update(Panel(
                padded_footer,
                border_style="bold",
                expand=True
            ))

            self.console.print(layout)
            time.sleep(1)  # Update every second

    def format_task_list(self, tasks):
        if not tasks:
            return "No incomplete tasks for today."
        
        formatted_tasks = []
        for task_id, task in tasks.items():
            formatted_task = f"☐ {task_id}: {task['description']}"
            formatted_tasks.append(formatted_task)
        
        return " || ".join(formatted_tasks)

    def reset_daily_stats(self):
        for user in self.user_stats:
            self.user_stats[user]["daily"] = 0
        self.total_completed_pomodoros = 0  # Reset total completed pomodoros
        self.last_pomodoro_date = date.today()  # Reset the last pomodoro date
        self.save_data()

    def center_text(self, text, width):
        return text.center(width)

    def wipe_user_tasks(self, user):
        wiped_count = 0
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task["user"] == user:
                tasks_to_remove.append(task_id)
                wiped_count += 1
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        self.save_data()
        return wiped_count

    def start_timer(self):
        self.timer_start = datetime.now()
        if self.current_phase == 'focus':
            duration = self.focus_duration
        elif self.current_phase == 'short_break':
            duration = self.short_break_duration
        else:  # long_break
            duration = self.long_break_duration
        self.timer_end = self.timer_start + timedelta(minutes=duration)
        self.timer_paused = False

    def stop_timer(self):
        self.timer_start = None
        self.timer_end = None
        self.timer_type = None
        self.timer_paused = False
        self.timer_pause_start = None
        self.current_phase = 'focus'
        self.pomodoro_count = 0

    def get_timer_status(self):
        self.check_and_reset_pomodoros()
        
        status_lines = []
        
        if not self.timer_start:
            status_lines.append(Text("⏸️ No active timer", style="bold"))
        else:
            if self.timer_paused:
                remaining = self.timer_end - self.timer_pause_start
            else:
                remaining = self.timer_end - datetime.now()
            
            if remaining.total_seconds() <= 0:
                self.next_phase()
                status_lines.append(Text(f"🔄 {self.current_phase.capitalize()} time started!", style="bold"))
                status_lines.append(Text(f"⏱️ Duration: {self.get_duration()} minutes", style="bold"))
            else:
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                timer_display = f"{minutes:02d}:{seconds:02d}"
                status_lines.append(Text(f"⏳ {self.current_phase.capitalize()}", style="bold"))
                timer_text = Text(f"⏱️ {timer_display}", style="bold cyan")
                timer_text.stylize("scale=1.5")  # This will make the text 1.5 times larger
                status_lines.append(timer_text)
        
        status_lines.append(Text(""))  # Add a blank line
        status_lines.append(Text(f"🏆 Completed: {self.total_completed_pomodoros} | 🔄 Cycle: {self.pomodoro_count + 1}/{self.max_pomodoros}", style="bold"))
        
        return Text("\n").join(status_lines)

    def check_and_reset_pomodoros(self):
        today = date.today()
        if today > self.last_pomodoro_date:
            self.total_completed_pomodoros = 0
            self.last_pomodoro_date = today

    def next_phase(self):
        if self.current_phase == 'focus':
            self.pomodoro_count += 1
            self.total_completed_pomodoros += 1
            self.last_pomodoro_date = date.today()
            if self.pomodoro_count >= self.max_pomodoros:
                self.current_phase = 'long_break'
                self.pomodoro_count = 0
            else:
                self.current_phase = 'short_break'
            # Play sound when focus phase completes
            self.complete_sound.play()
        else:
            self.current_phase = 'focus'
            # Play sound when break phase completes
            self.complete_sound.play()
        self.start_timer()

    def get_duration(self):
        if self.current_phase == 'focus':
            return self.focus_duration
        elif self.current_phase == 'short_break':
            return self.short_break_duration
        else:  # long_break
            return self.long_break_duration

    def set_timer_duration(self, timer_type, duration):
        if timer_type == 'focus':
            self.focus_duration = duration
        elif timer_type == 'short':
            self.short_break_duration = duration
        elif timer_type == 'long':
            self.long_break_duration = duration
        else:
            raise ValueError("Invalid timer type")
