import uuid
import os
import time
import json
from datetime import datetime, date
from collections import Counter
from textwrap import wrap

class TaskManager:
    def __init__(self, file_path='tasks.json'):
        self.file_path = file_path
        self.tasks = {}
        self.user_stats = {}
        self.load_data()
        self.clean_old_tasks()

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

            # Print header with emojis
            print()
            print(self.center_text("🍅 Pomodoro Task Dashboard 🍅", total_width))
            print()

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
            print(self.center_text("⏱️  Dashboard updates every 5 seconds ⏱️", total_width))
            print(self.center_text("🎉 Keep up the great work! 🎉", total_width))
            print()
            print(self.center_text("📝 Use !task command to manage your tasks 📝", total_width))
            
            time.sleep(5)  # Update every 5 seconds

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
