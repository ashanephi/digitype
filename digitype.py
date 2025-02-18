import sqlite3
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame
import os
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.dates as mdates

# Register adapters and converters for datetime
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("timestamp", lambda s: datetime.fromisoformat(s.decode("utf-8")))

class DigiType(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digitype Dojo")
        self.geometry("800x600")
        self.db_conn = sqlite3.connect('typing_data.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_cursor = self.db_conn.cursor()
        self.create_tables()

        self.test_duration = 30
        self.remaining_time = self.test_duration
        self.is_paused = False

        self.texts = {
            "Easy": [
                "The quick brown fox jumps over the lazy dog.",
                "A journey of a thousand miles begins with a single step.",
                "To be or not to be, that is the question."
            ],
            "Medium": [
                "All that glitters is not gold.",
                "A picture is worth a thousand words.",
                "Actions speak louder than words."
            ],
            "Hard": [
                "Beauty is in the eye of the beholder.",
                "Better late than never.",
                "Birds of a feather flock together."
            ]
        }

        self.dark_mode = False
        self.font_size = 14
        self.font_color = "black"
        self.bg_color = "white"
        self.typing_mode = "Timed Test"
        self.difficulty_level = "Easy"
        self.current_user = None
        self.achievements = []
        self.load_achievements()
        self.create_login_page()

        pygame.mixer.init()
        self.key_sound = self.load_sound("key_press.mp3")
        self.complete_sound = self.load_sound("complete.mp3")

    def load_sound(self, filename):
        if os.path.exists(filename):
            return pygame.mixer.Sound(filename)
        print(f"Warning: Sound file {filename} not found.")
        return None

    def create_tables(self):
        self.db_cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )''')
        self.db_cursor.execute('''CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            wpm INTEGER,
            accuracy REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        self.db_conn.commit()

    def create_login_page(self):
        self.clear_widgets()

        login_frame = tk.Frame(self, bg=self.bg_color)
        login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(login_frame, text="Login", font=("Arial", 24), bg=self.bg_color, fg=self.font_color).pack(pady=20)
        self.create_entry(login_frame, "Username:", "username_entry")
        self.create_entry(login_frame, "Password:", "password_entry", show="*")

        tk.Button(login_frame, text="Login", command=self.login, font=("Arial", 14), bg="#3498db", fg="white").pack(pady=10)
        tk.Button(login_frame, text="Create Account", command=self.create_account_page, font=("Arial", 14), bg="#2ecc71", fg="white").pack(pady=10)

    def create_account_page(self):
        self.clear_widgets()

        account_frame = tk.Frame(self, bg=self.bg_color)
        account_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(account_frame, text="Create Account", font=("Arial", 24), bg=self.bg_color, fg=self.font_color).pack(pady=20)
        self.create_entry(account_frame, "Username:", "new_username_entry")
        self.create_entry(account_frame, "Password:", "new_password_entry", show="*")
        self.create_entry(account_frame, "Email (optional):", "email_entry")

        tk.Button(account_frame, text="Create Account", command=self.create_account, font=("Arial", 14), bg="#3498db", fg="white").pack(pady=10)
        tk.Button(account_frame, text="Back to Login", command=self.create_login_page, font=("Arial", 14), bg="#e74c3c", fg="white").pack(pady=10)

    def create_entry(self, parent, label_text, attr_name, **kwargs):
        tk.Label(parent, text=label_text, font=("Arial", 14), bg=self.bg_color, fg=self.font_color).pack(pady=5)
        entry = tk.Entry(parent, font=("Arial", 14), bg=self.bg_color, fg=self.font_color, **kwargs)
        entry.pack(pady=5)
        setattr(self, attr_name, entry)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.db_cursor.execute('SELECT id FROM users WHERE username=? AND password=?', (username, password))
        user = self.db_cursor.fetchone()
        if user:
            self.current_user = user[0]
            self.create_homepage()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def create_account(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        email = self.email_entry.get()
        try:
            self.db_cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
            self.db_conn.commit()
            messagebox.showinfo("Account Created", "Account created successfully. Please login.")
            self.create_login_page()
        except sqlite3.IntegrityError:
            messagebox.showerror("Account Creation Failed", "Username already exists")

    def create_navbar(self, parent_frame):
        navbar = tk.Frame(parent_frame, bg="#333")
        navbar.pack(fill=tk.X)

        buttons = [
            ("Home", self.create_homepage),
            ("Typing Test", self.create_widgets),
            ("Progress", self.update_progress_chart),
            ("Word Rain", self.start_word_rain),
            ("Typing History", self.show_typing_history),
            ("Leaderboard", self.show_leaderboard),
            ("Achievements", self.show_achievements),
            ("Settings", self.open_settings),
            ("Logout", self.logout)
        ]

        for text, command in buttons:
            side = tk.LEFT if text not in ["Settings", "Logout"] else tk.RIGHT
            tk.Button(navbar, text=text, command=command, bg="#333", fg="white", relief=tk.FLAT).pack(side=side, padx=10, pady=5)

    def create_homepage(self):
        self.clear_widgets()

        self.home_frame = tk.Frame(self, bg=self.bg_color)
        self.home_frame.pack(fill=tk.BOTH, expand=True)

        self.create_navbar(self.home_frame)

        tk.Label(self.home_frame, text="Digitype Dojo", font=("Arial", 24), bg=self.bg_color, fg=self.font_color).pack(pady=20)
        tk.Button(self.home_frame, text="Start Typing Test", command=self.create_widgets, font=("Arial", 16), bg="#3498db", fg="white").pack(pady=10)
        tk.Button(self.home_frame, text="View Progress", command=self.update_progress_chart, font=("Arial", 16), bg="#2ecc71", fg="white").pack(pady=10)

    def create_widgets(self):
        self.clear_widgets()

        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.create_navbar(main_frame)

        self.text_display = tk.Label(main_frame, text="Click Start to Begin", font=("Arial", self.font_size), bg=self.bg_color, fg=self.font_color, wraplength=700, justify="left")
        self.text_display.pack(pady=10)

        self.typing_input = tk.Entry(main_frame, font=("Arial", self.font_size), width=80, bg=self.bg_color, fg=self.font_color)
        self.typing_input.pack(pady=10)
        self.typing_input.bind("<KeyRelease>", self.on_text_change)

        self.timer_label = tk.Label(main_frame, text="Time Left: 30s", font=("Arial", self.font_size), bg=self.bg_color, fg=self.font_color)
        self.timer_label.pack(pady=10)

        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(pady=10)
        self.create_button(btn_frame, "Start", self.start_test, "#3498db")
        self.create_button(btn_frame, "Pause", self.pause_test, "#f39c12")
        self.create_button(btn_frame, "Reset", self.reset_test, "#e74c3c")
        self.create_button(btn_frame, "Upload Text File", self.upload_text_file, "#9b59b6")

        self.create_combobox(main_frame, "Select Duration", ["30-seconds", "1-minute", "3-minute", "5-minute"], self.set_test_duration)
        self.create_combobox(main_frame, "Select Mode", ["Timed Test", "Practice Mode", "Custom Text"], self.set_typing_mode)
        self.create_combobox(main_frame, "Select Difficulty", ["Easy", "Medium", "Hard"], self.set_difficulty_level)

        self.chart_area = tk.Frame(main_frame, bg=self.bg_color)
        self.chart_area.pack(pady=10, fill=tk.BOTH, expand=True)

    def create_button(self, parent, text, command, bg_color):
        tk.Button(parent, text=text, command=command, bg=bg_color, fg="white").pack(side=tk.LEFT, padx=5)

    def create_combobox(self, parent, default_text, values, command):
        combobox = ttk.Combobox(parent, values=values, state="readonly")
        combobox.set(default_text)
        combobox.pack(pady=10)
        combobox.bind("<<ComboboxSelected>>", command)

    def set_test_duration(self, event):
        duration_map = {
            "30-seconds": 30,
            "1-minute": 60,
            "3-minute": 180,
            "5-minute": 300
        }
        self.test_duration = duration_map[self.duration_spinner.get()]
        self.remaining_time = self.test_duration
        self.timer_label.config(text=f"Time Left: {self.remaining_time}s")

    def set_typing_mode(self, event):
        self.typing_mode = self.mode_spinner.get()

    def set_difficulty_level(self, event):
        self.difficulty_level = self.difficulty_spinner.get()

    def start_test(self):
        if self.typing_mode == "Timed Test":
            self.text_display.config(text=random.choice(self.texts[self.difficulty_level]) * 10)
        elif self.typing_mode == "Practice Mode":
            self.text_display.config(text="Practice Mode: Type anything you want.")
        elif self.typing_mode == "Custom Text":
            self.text_display.config(text="Custom Text Mode: Enter your custom text below.")
            self.typing_input.bind("<Return>", self.set_custom_text)

        self.typing_input.delete(0, tk.END)
        self.typing_input.focus()
        self.start_time = time.time()
        self.remaining_time = self.test_duration
        self.timer_label.config(text=f"Time Left: {self.remaining_time}s")
        self.is_paused = False
        self.update_timer()

    def set_custom_text(self, event):
        custom_text = self.typing_input.get()
        self.text_display.config(text=custom_text)
        self.typing_input.delete(0, tk.END)
        self.typing_input.unbind("<Return>")

    def upload_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                self.uploaded_text = file.read().split('\n')
            self.text_display.config(text=self.uploaded_text[0])
            self.uploaded_text_index = 0

    def update_timer(self):
        if not self.is_paused and self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_label.config(text=f"Time Left: {self.remaining_time}s")
            self.after(1000, self.update_timer)
        elif self.remaining_time == 0:
            self.end_test()

    def pause_test(self):
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.update_timer()

    def end_test(self):
        typed_text = self.typing_input.get().strip()
        elapsed_time = self.test_duration - self.remaining_time
        wpm = len(typed_text.split()) * (60 / elapsed_time) if elapsed_time > 0 else 0
        accuracy = self.calculate_accuracy(typed_text)
        self.save_progress(wpm, accuracy)
        self.show_results(wpm, accuracy)
        self.typing_input.config(state=tk.DISABLED)
        if self.complete_sound:
            self.complete_sound.play()

    def calculate_accuracy(self, typed_text):
        target_text = self.text_display.cget("text").strip()
        correct_chars = sum(1 for i, c in enumerate(typed_text) if i < len(target_text) and c == target_text[i])
        return (correct_chars / len(target_text)) * 100 if target_text else 0

    def on_text_change(self, event):
        target_text = self.text_display.cget("text").strip()
        typed_text = self.typing_input.get()
        self.typing_input.config(fg="red" if not target_text.startswith(typed_text) else self.font_color)
        if self.key_sound:
            self.key_sound.play()
        if typed_text == target_text:
            self.uploaded_text_index += 1
            if self.uploaded_text_index < len(self.uploaded_text):
                self.text_display.config(text=self.uploaded_text[self.uploaded_text_index])
                self.typing_input.delete(0, tk.END)
            else:
                self.end_test()

    def save_progress(self, wpm, accuracy):
        self.db_cursor.execute('''INSERT INTO progress (user_id, wpm, accuracy, date) VALUES (?, ?, ?, ?)''', 
                               (self.current_user, wpm, accuracy, datetime.now().strftime('%Y-%m-%d')))
        self.db_conn.commit()

    def show_results(self, wpm, accuracy):
        self.check_achievements(wpm, accuracy)
        messagebox.showinfo("Results", f"WPM: {int(wpm)}\nAccuracy: {accuracy:.2f}%")
        self.update_progress_chart()

    def update_progress_chart(self):
        self.clear_widgets()

        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.create_navbar(main_frame)

        self.chart_area = tk.Frame(main_frame, bg=self.bg_color)
        self.chart_area.pack(pady=10, fill=tk.BOTH, expand=True)

        date_frame = tk.Frame(main_frame, bg=self.bg_color)
        date_frame.pack(pady=10)

        tk.Label(date_frame, text="From:", bg=self.bg_color, fg=self.font_color).pack(side=tk.LEFT, padx=5)
        self.start_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(date_frame, text="To:", bg=self.bg_color, fg=self.font_color).pack(side=tk.LEFT, padx=5)
        self.end_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(date_frame, text="Show", command=self.show_progress_chart, bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)

        # Display the past 7 days' progress by default
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        self.start_date_entry.set_date(start_date)
        self.end_date_entry.set_date(end_date)
        self.show_progress_chart()

    def show_progress_chart(self):
        start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')
        self.db_cursor.execute('SELECT date, wpm FROM progress WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date', 
                               (self.current_user, start_date, end_date))
        data = self.db_cursor.fetchall()
        dates = [d[0] for d in data]
        wpm_values = [d[1] for d in data]

        fig, ax = plt.subplots()
        ax.plot(dates, wpm_values, marker='o', linestyle='-', color='blue')
        ax.set_title('WPM Progress')
        ax.set_xlabel('Date')
        ax.set_ylabel('Words Per Minute')
        ax.grid(True)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        self.clear_chart_area()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def reset_test(self):
        self.text_display.config(text="Click Start to Begin")
        self.typing_input.config(state=tk.NORMAL)
        self.typing_input.delete(0, tk.END)
        self.timer_label.config(text=f"Time Left: {self.test_duration}s")
        self.is_paused = False

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.bg_color = "black" if self.dark_mode else "white"
        self.font_color = "white" if self.dark_mode else "black"
        self.create_homepage()

    def start_word_rain(self):
        self.clear_widgets()

        self.word_rain_frame = tk.Frame(self, bg=self.bg_color)
        self.word_rain_frame.pack(fill=tk.BOTH, expand=True)

        self.create_navbar(self.word_rain_frame)

        self.canvas = tk.Canvas(self.word_rain_frame, bg=self.bg_color)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew"]
        self.active_words = []
        self.word_speed = 1000
        self.score = 0
        self.is_paused = False

        self.typing_input = tk.Entry(self.word_rain_frame, font=("Arial", self.font_size), width=80, bg=self.bg_color, fg=self.font_color)
        self.typing_input.pack(pady=10)
        self.typing_input.bind("<KeyRelease>", self.check_word_rain)

        self.score_label = tk.Label(self.word_rain_frame, text="Score: 0", font=("Arial", self.font_size), bg=self.bg_color, fg=self.font_color)
        self.score_label.pack(pady=10)

        self.remaining_time = self.test_duration
        self.timer_label = tk.Label(self.word_rain_frame, text=f"Time Left: {self.remaining_time}s", font=("Arial", self.font_size), bg=self.bg_color, fg=self.font_color)
        self.timer_label.pack(pady=10)

        btn_frame = tk.Frame(self.word_rain_frame, bg=self.bg_color)
        btn_frame.pack(pady=10)
        pause_btn = tk.Button(btn_frame, text="Pause", command=self.pause_word_rain, bg="#f39c12", fg="white")
        pause_btn.pack(side=tk.LEFT, padx=5)
        reset_btn = tk.Button(btn_frame, text="Reset", command=self.reset_word_rain, bg="#e74c3c", fg="white")
        reset_btn.pack(side=tk.LEFT, padx=5)

        self.add_word()
        self.update_word_rain()
        self.update_word_rain_timer()

    def add_word(self):
        if not self.is_paused:
            word = random.choice(self.words)
            word_id = self.canvas.create_text(random.randint(50, 750), 0, text=word, font=("Arial", self.font_size), fill=self.font_color)
            self.active_words.append(word_id)
            self.after(self.word_speed, self.add_word)

    def update_word_rain(self):
        if not self.is_paused:
            for word_id in self.active_words:
                self.canvas.move(word_id, 0, 5)
                if self.canvas.coords(word_id)[1] > 600:
                    self.canvas.delete(word_id)
                    self.active_words.remove(word_id)
            self.after(50, self.update_word_rain)

    def update_word_rain_timer(self):
        if not self.is_paused:
            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.timer_label.config(text=f"Time Left: {self.remaining_time}s")
                self.after(1000, self.update_word_rain_timer)
            else:
                self.end_word_rain()

    def pause_word_rain(self):
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.add_word()
            self.update_word_rain()
            self.update_word_rain_timer()

    def end_word_rain(self):
        wpm = self.score * (60 / self.test_duration)
        self.save_progress(wpm, 100)
        messagebox.showinfo("Game Over", f"Score: {self.score}\nWPM: {int(wpm)}")
        self.create_homepage()

    def reset_word_rain(self):
        for word_id in self.active_words:
            self.canvas.delete(word_id)
        self.active_words.clear()
        self.score = 0
        self.score_label.config(text="Score: 0")
        self.remaining_time = self.test_duration
        self.timer_label.config(text=f"Time Left: {self.remaining_time}s")
        self.is_paused = False

    def check_word_rain(self, event):
        typed_text = self.typing_input.get().strip()
        for word_id in self.active_words:
            word = self.canvas.itemcget(word_id, "text")
            if typed_text == word:
                self.canvas.delete(word_id)
                self.active_words.remove(word_id)
                self.typing_input.delete(0, tk.END)
                self.score += 1
                self.score_label.config(text=f"Score: {self.score}")
                break

    def show_typing_history(self):
        self.clear_widgets()

        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.create_navbar(main_frame)

        self.chart_area = tk.Frame(main_frame, bg=self.bg_color)
        self.chart_area.pack(pady=10, fill=tk.BOTH, expand=True)

        date_frame = tk.Frame(main_frame, bg=self.bg_color)
        date_frame.pack(pady=10)

        tk.Label(date_frame, text="From:", bg=self.bg_color, fg=self.font_color).pack(side=tk.LEFT, padx=5)
        self.start_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(date_frame, text="To:", bg=self.bg_color, fg=self.font_color).pack(side=tk.LEFT, padx=5)
        self.end_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(date_frame, text="Show", command=self.show_history_chart, bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)

        # Display the past 7 days' history by default
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        self.start_date_entry.set_date(start_date)
        self.end_date_entry.set_date(end_date)
        self.show_history_chart()

    def show_history_chart(self):
        start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')
        self.db_cursor.execute('SELECT date, wpm, accuracy FROM progress WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date', 
                               (self.current_user, start_date, end_date))
        data = self.db_cursor.fetchall()
        dates = [d[0] for d in data]
        wpm_values = [d[1] for d in data]
        accuracy_values = [d[2] for d in data]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        ax1.plot(dates, wpm_values, marker='o', linestyle='-', color='blue')
        ax1.set_title('WPM Over Selected Period')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Words Per Minute')
        ax1.grid(True)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        ax2.plot(dates, accuracy_values, marker='o', linestyle='-', color='green')
        ax2.set_title('Accuracy Over Selected Period')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Accuracy (%)')
        ax2.grid(True)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        self.clear_chart_area()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_leaderboard(self):
        self.clear_widgets()

        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.create_navbar(main_frame)

        self.chart_area = tk.Frame(main_frame, bg=self.bg_color)
        self.chart_area.pack(pady=10, fill=tk.BOTH, expand=True)

        self.db_cursor.execute('''
            SELECT u.username, MAX(p.wpm) as max_wpm, p.accuracy, p.date
            FROM progress p
            JOIN users u ON p.user_id = u.id
            GROUP BY u.username
            ORDER BY max_wpm DESC, p.accuracy DESC
            LIMIT 10
        ''')
        data = self.db_cursor.fetchall()
        usernames = [d[0] for d in data]
        wpm_values = [d[1] for d in data]
        accuracy_values = [d[2] for d in data]
        dates = [d[3] for d in data]

        leaderboard_frame = tk.Frame(self.chart_area, bg=self.bg_color)
        leaderboard_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Label(leaderboard_frame, text="Leaderboard", font=("Arial", 24), bg=self.bg_color, fg=self.font_color).pack(pady=10)

        for i, (username, wpm, accuracy, date) in enumerate(zip(usernames, wpm_values, accuracy_values, dates)):
            tk.Label(leaderboard_frame, text=f"{i+1}. {username} - WPM: {wpm}, Accuracy: {accuracy:.2f}%, Date: {date}", font=("Arial", 14), bg=self.bg_color, fg=self.font_color).pack(pady=5)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x400")

        tk.Label(settings_window, text="Font Size:").pack(pady=10)
        font_size_spinbox = tk.Spinbox(settings_window, from_=10, to=30, command=lambda: self.set_font_size(font_size_spinbox.get()))
        font_size_spinbox.pack(pady=10)

        tk.Label(settings_window, text="Font Color:").pack(pady=10)
        font_color_entry = tk.Entry(settings_window)
        font_color_entry.pack(pady=10)
        font_color_entry.insert(0, self.font_color)
        tk.Button(settings_window, text="Set Font Color", command=lambda: self.set_font_color(font_color_entry.get())).pack(pady=10)

        tk.Label(settings_window, text="Background Color:").pack(pady=10)
        bg_color_entry = tk.Entry(settings_window)
        bg_color_entry.pack(pady=10)
        bg_color_entry.insert(0, self.bg_color)
        tk.Button(settings_window, text="Set Background Color", command=lambda: self.set_bg_color(bg_color_entry.get())).pack(pady=10)

        tk.Label(settings_window, text="Profile:").pack(pady=10)
        tk.Button(settings_window, text="Update Profile", command=self.update_profile).pack(pady=5)

    def update_profile(self):
        profile_window = tk.Toplevel(self)
        profile_window.title("Update Profile")
        profile_window.geometry("400x300")

        tk.Label(profile_window, text="Username:").pack(pady=10)
        username_entry = tk.Entry(profile_window)
        username_entry.pack(pady=10)
        username_entry.insert(0, self.get_current_username())

        tk.Label(profile_window, text="Password:").pack(pady=10)
        password_entry = tk.Entry(profile_window, show="*")
        password_entry.pack(pady=10)

        tk.Label(profile_window, text="Email:").pack(pady=10)
        email_entry = tk.Entry(profile_window)
        email_entry.pack(pady=10)
        email_entry.insert(0, self.get_current_email())

        tk.Button(profile_window, text="Save", command=lambda: self.save_profile(username_entry.get(), password_entry.get(), email_entry.get())).pack(pady=10)

    def get_current_username(self):
        self.db_cursor.execute('SELECT username FROM users WHERE id=?', (self.current_user,))
        return self.db_cursor.fetchone()[0]

    def get_current_email(self):
        self.db_cursor.execute('SELECT email FROM users WHERE id=?', (self.current_user,))
        return self.db_cursor.fetchone()[0]

    def save_profile(self, username, password, email):
        self.db_cursor.execute('UPDATE users SET username=?, password=?, email=? WHERE id=?', (username, password, email, self.current_user))
        self.db_conn.commit()
        messagebox.showinfo("Profile Updated", "Your profile has been updated successfully.")

    def load_achievements(self):
        self.achievements = [
            {"name": "First Test", "description": "Complete your first typing test", "achieved": False},
            {"name": "Speed Demon", "description": "Achieve a WPM of 100 or more", "achieved": False},
            {"name": "Accuracy Master", "description": "Achieve an accuracy of 95% or more", "achieved": False}
        ]

    def check_achievements(self, wpm, accuracy):
        for achievement in self.achievements:
            if achievement["name"] == "First Test":
                achievement["achieved"] = True
            elif achievement["name"] == "Speed Demon" and wpm >= 100:
                achievement["achieved"] = True
            elif achievement["name"] == "Accuracy Master" and accuracy >= 95:
                achievement["achieved"] = True

    def show_achievements(self):
        self.clear_widgets()

        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.create_navbar(main_frame)

        achievements_frame = tk.Frame(main_frame, bg=self.bg_color)
        achievements_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Label(achievements_frame, text="Achievements", font=("Arial", 24), bg=self.bg_color, fg=self.font_color).pack(pady=10)

        for achievement in self.achievements:
            status = "Achieved" if achievement["achieved"] else "Not Achieved"
            tk.Label(achievements_frame, text=f"{achievement['name']}: {achievement['description']} - {status}", font=("Arial", 14), bg=self.bg_color, fg=self.font_color).pack(pady=5)

    def logout(self):
        self.current_user = None
        self.create_login_page()

    def clear_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()

    def clear_chart_area(self):
        for widget in self.chart_area.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = DigiType()
    app.mainloop()
