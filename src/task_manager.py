import uuid
import os
import time
import json
from datetime import datetime, date, timedelta
from collections import Counter
from textwrap import wrap
import pygame

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
            os.system('clear' if os.name == 'posix' else 'cls')  # Clear the terminal
            today = date.today()
            
            # Set column widths
            column_width = 59  # Reduced by 1 to account for separator
            total_width = column_width * 2 + 3  # 3 for the left, middle, and right borders
            max_description_length = 20  # Maximum length for task descriptions

            # Print Pomodoro timer status
            print("\n" + self.get_timer_status())
            print("\n" + "=" * total_width)  # Separator line

            # Print header with emojis
            print()
            print(self.center_text("🍅 Pomodoro Task Dashboard 🍅", total_width))
            
            # Prepare the left column (stats)
            left_column = []
            left_column.append(self.center_text("User Stats", column_width))
            left_column.append("-" * column_width)
            
            # Only include users with at least one completed task today
            daily_stats = Counter({user: stats['daily'] for user, stats in self.user_stats.items() if stats['daily'] > 0})
            total_stats = Counter({user: stats['total'] for user, stats in self.user_stats.items() if stats['total'] > 0})
            
            left_column.append(self.center_text("Top 5 Users (Today)", column_width))
            if daily_stats:
                for i, (user, count) in enumerate(daily_stats.most_common(5), 1):
                    left_column.append(f"  {i}. {user}: {count}".ljust(column_width))
            else:
                left_column.append(self.center_text("-- No tasks completed today --", column_width))
            
            left_column.append(" " * column_width)
            left_column.append(self.center_text("Top 5 Users (All-time)", column_width))
            if total_stats:
                for i, (user, count) in enumerate(total_stats.most_common(5), 1):
                    left_column.append(f"  {i}. {user}: {count}".ljust(column_width))
            else:
                left_column.append(self.center_text("No tasks completed yet", column_width))
            
            total_completed = sum(stats['total'] for stats in self.user_stats.values())
            left_column.append(" " * column_width)
            left_column.append(self.center_text(f"Total tasks completed: {total_completed}", column_width))
            
            # Prepare the right column (tasks)
            right_column = []
            right_column.append(self.center_text("Today's Tasks", column_width))
            right_column.append("-" * column_width)
            for task_id, task in self.tasks.items():
                if task["date"] == today:
                    status = "X" if task["completed"] else " "
                    description = task['description']
                    if len(description) > max_description_length:
                        description = description[:max_description_length-3] + "..."
                    task_line = f"[{status}] {task_id}: {description} ({task['user']})"
                    right_column.append(task_line.ljust(column_width))

            # Combine columns and display
            max_lines = max(len(left_column), len(right_column))
            left_column += [' ' * column_width] * (max_lines - len(left_column))
            right_column += [' ' * column_width] * (max_lines - len(right_column))
            
            print("+" + "-" * column_width + "+" + "-" * column_width + "+")
            for left, right in zip(left_column, right_column):
                print(f"|{left}|{right}|")
            print("+" + "-" * column_width + "+" + "-" * column_width + "+")
            
            # Print footer with emojis
            print()            
            print(self.center_text("🎉 Keep up the great work! 🎉", total_width))
            print()
            print(self.center_text("📝 Use !task command to manage your tasks 📝", total_width))
            
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
        status_lines.append("🍅 Pomodoro Timer 🍅")
        status_lines.append("")
        
        if not self.timer_start:
            status_lines.append("⏸️ No active timer")
        else:
            if self.timer_paused:
                remaining = self.timer_end - self.timer_pause_start
            else:
                remaining = self.timer_end - datetime.now()
            
            if remaining.total_seconds() <= 0:
                self.next_phase()
                status_lines.append(f"🔄 {self.current_phase.capitalize()} time started!")
                status_lines.append(f"⏱️ Duration: {self.get_duration()} minutes")
                # Note: We don't need to play the sound here as it's handled in next_phase()
            else:
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                timer_display = f"{minutes:02d}:{seconds:02d}"
                status_lines.append(f"⏳ {self.current_phase.capitalize()}")
                status_lines.append(f"⏱️ {timer_display}")
        
        status_lines.append("")
        status_lines.append(f"🏆 Completed Pomodoros today: {self.total_completed_pomodoros}")
        status_lines.append(f"🔄 Current cycle: {self.pomodoro_count + 1}/{self.max_pomodoros}")
        
        return "\n".join(self.center_text(line, 120) for line in status_lines)

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
