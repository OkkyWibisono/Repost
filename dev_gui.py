"""
Medusa Development GUI - Terminal Style
Simple GUI for sending tasks to the automation system during development.
"""

import tkinter as tk
from tkinter import ttk
import json
import urllib.request
import urllib.error
import subprocess
import sys
import os
import threading
from datetime import datetime


# Task parameter definitions
TASK_PARAMS = {
    "likepost": {
        "username": {"type": "string", "label": "Username", "placeholder": "Target username"},
        "post": {"type": "string", "label": "Post Content", "placeholder": "Text to identify the post"},
    },
    "comment": {
        "username": {"type": "string", "label": "Username", "placeholder": "Target username"},
        "post": {"type": "string", "label": "Post Content", "placeholder": "Text to identify the post"},
        "comment": {"type": "string", "label": "Comment", "placeholder": "Your comment text"},
    },
    "login": {},
    "logout": {},
    "navigate": {
        "url": {"type": "string", "label": "URL", "placeholder": "https://..."},
    },
    "search": {
        "query": {"type": "string", "label": "Search Query", "placeholder": "Search term"},
    },
    "post": {
        "content": {"type": "string", "label": "Post Content", "placeholder": "Your post text"},
    },
    "findpost": {
        "username": {"type": "string", "label": "Username", "placeholder": "Target username"},
        "post": {"type": "string", "label": "Post Content", "placeholder": "Text to identify the post"},
    },
}

PLATFORMS = ["x", "instagram", "tiktok"]
TASKS = ["likepost", "comment", "login", "logout", "navigate", "search", "post", "findpost"]


class TerminalStyle:
    """Terminal color scheme"""
    BG = "#0c0c0c"
    FG = "#00ff00"
    FG_DIM = "#008800"
    FG_ERROR = "#ff4444"
    FG_SUCCESS = "#44ff44"
    FG_INFO = "#44aaff"
    FG_WARN = "#ffaa00"
    ENTRY_BG = "#1a1a1a"
    ENTRY_FG = "#00ff00"
    BUTTON_BG = "#1a1a1a"
    BUTTON_FG = "#00ff00"
    BUTTON_ACTIVE_BG = "#00ff00"
    BUTTON_ACTIVE_FG = "#0c0c0c"
    FONT = ("Consolas", 10)
    FONT_BOLD = ("Consolas", 10, "bold")
    FONT_LARGE = ("Consolas", 12, "bold")


class MedusaDevGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MEDUSA DEV")
        self.root.configure(bg=TerminalStyle.BG)
        self.root.geometry("600x700")
        self.root.resizable(True, True)

        self.api_endpoint = "http://localhost:8888"
        self.param_entries = {}
        self.main_process = None
        self.api_process = None
        self.api_running = False
        self.main_running = False
        self.python_path = self.get_python_path()

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log("MEDUSA Development Console v1.0")
        self.log("=" * 50)
        self.log("API Endpoint: " + self.api_endpoint)
        self.log(f"Python: {self.python_path}")
        self.log("Ready to send tasks...")
        self.log("")

    def get_python_path(self):
        """Get the Python executable path, preferring venv if available"""
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Check for venv in project directory
        venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            return venv_python

        # Fallback to current Python interpreter
        return sys.executable

    def on_close(self):
        """Clean up processes on window close"""
        self.api_running = False
        self.main_running = False
        if self.api_process and self.api_process.poll() is None:
            self.api_process.terminate()
        if self.main_process and self.main_process.poll() is None:
            self.main_process.terminate()
        self.root.destroy()

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=TerminalStyle.BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header = tk.Label(
            main_frame,
            text="[ MEDUSA TASK SENDER ]",
            font=TerminalStyle.FONT_LARGE,
            bg=TerminalStyle.BG,
            fg=TerminalStyle.FG
        )
        header.pack(pady=(0, 10))

        # Process control frame
        process_frame = tk.Frame(main_frame, bg=TerminalStyle.BG)
        process_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            process_frame,
            text="[ PROCESS CONTROL ]",
            font=TerminalStyle.FONT_BOLD,
            bg=TerminalStyle.BG,
            fg=TerminalStyle.FG_DIM
        ).pack(anchor=tk.W)

        buttons_row = tk.Frame(process_frame, bg=TerminalStyle.BG)
        buttons_row.pack(fill=tk.X, pady=5)

        # Start API button
        self.api_button = tk.Button(
            buttons_row,
            text="[ START API ]",
            font=TerminalStyle.FONT,
            bg=TerminalStyle.BUTTON_BG,
            fg=TerminalStyle.FG_INFO,
            activebackground=TerminalStyle.FG_INFO,
            activeforeground=TerminalStyle.BG,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_api,
            padx=15,
            pady=5
        )
        self.api_button.pack(side=tk.LEFT, padx=(0, 10))

        # Start Main button
        self.main_button = tk.Button(
            buttons_row,
            text="[ START MAIN ]",
            font=TerminalStyle.FONT,
            bg=TerminalStyle.BUTTON_BG,
            fg=TerminalStyle.FG_WARN,
            activebackground=TerminalStyle.FG_WARN,
            activeforeground=TerminalStyle.BG,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_main,
            padx=15,
            pady=5
        )
        self.main_button.pack(side=tk.LEFT)

        # Controls frame
        controls_frame = tk.Frame(main_frame, bg=TerminalStyle.BG)
        controls_frame.pack(fill=tk.X, pady=5)

        # Platform selector
        platform_frame = tk.Frame(controls_frame, bg=TerminalStyle.BG)
        platform_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            platform_frame,
            text="PLATFORM >",
            font=TerminalStyle.FONT_BOLD,
            bg=TerminalStyle.BG,
            fg=TerminalStyle.FG_DIM
        ).pack(side=tk.LEFT)

        self.platform_var = tk.StringVar(value=PLATFORMS[0])
        self.platform_combo = ttk.Combobox(
            platform_frame,
            textvariable=self.platform_var,
            values=PLATFORMS,
            state="readonly",
            width=15,
            font=TerminalStyle.FONT
        )
        self.platform_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.style_combobox()

        # Task selector
        task_frame = tk.Frame(controls_frame, bg=TerminalStyle.BG)
        task_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            task_frame,
            text="TASK     >",
            font=TerminalStyle.FONT_BOLD,
            bg=TerminalStyle.BG,
            fg=TerminalStyle.FG_DIM
        ).pack(side=tk.LEFT)

        self.task_var = tk.StringVar(value=TASKS[0])
        self.task_combo = ttk.Combobox(
            task_frame,
            textvariable=self.task_var,
            values=TASKS,
            state="readonly",
            width=15,
            font=TerminalStyle.FONT
        )
        self.task_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.task_combo.bind("<<ComboboxSelected>>", self.on_task_change)

        # Parameters frame (dynamic)
        self.params_container = tk.Frame(main_frame, bg=TerminalStyle.BG)
        self.params_container.pack(fill=tk.X, pady=10)

        params_header = tk.Label(
            self.params_container,
            text="[ PARAMETERS ]",
            font=TerminalStyle.FONT_BOLD,
            bg=TerminalStyle.BG,
            fg=TerminalStyle.FG_DIM
        )
        params_header.pack(anchor=tk.W)

        self.params_frame = tk.Frame(self.params_container, bg=TerminalStyle.BG)
        self.params_frame.pack(fill=tk.X, pady=5)

        # Build initial params
        self.build_param_fields()

        # Run button
        button_frame = tk.Frame(main_frame, bg=TerminalStyle.BG)
        button_frame.pack(fill=tk.X, pady=10)

        self.run_button = tk.Button(
            button_frame,
            text="[ RUN TASK ]",
            font=TerminalStyle.FONT_BOLD,
            bg=TerminalStyle.BUTTON_BG,
            fg=TerminalStyle.FG,
            activebackground=TerminalStyle.BUTTON_ACTIVE_BG,
            activeforeground=TerminalStyle.BUTTON_ACTIVE_FG,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.run_task,
            padx=20,
            pady=8
        )
        self.run_button.pack()

        # Add hover effect
        self.run_button.bind("<Enter>", lambda e: self.run_button.config(bg=TerminalStyle.FG, fg=TerminalStyle.BG))
        self.run_button.bind("<Leave>", lambda e: self.run_button.config(bg=TerminalStyle.BUTTON_BG, fg=TerminalStyle.FG))

        # Log output
        log_frame = tk.Frame(main_frame, bg=TerminalStyle.BG)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(
            log_frame,
            text="[ OUTPUT ]",
            font=TerminalStyle.FONT_BOLD,
            bg=TerminalStyle.BG,
            fg=TerminalStyle.FG_DIM
        ).pack(anchor=tk.W)

        # Log text with scrollbar
        log_container = tk.Frame(log_frame, bg=TerminalStyle.BG)
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_container,
            font=TerminalStyle.FONT,
            bg=TerminalStyle.ENTRY_BG,
            fg=TerminalStyle.FG,
            insertbackground=TerminalStyle.FG,
            relief=tk.FLAT,
            height=15,
            wrap=tk.WORD
        )

        scrollbar = tk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure text tags for colors
        self.log_text.tag_configure("error", foreground=TerminalStyle.FG_ERROR)
        self.log_text.tag_configure("success", foreground=TerminalStyle.FG_SUCCESS)
        self.log_text.tag_configure("info", foreground=TerminalStyle.FG_INFO)
        self.log_text.tag_configure("warn", foreground=TerminalStyle.FG_WARN)
        self.log_text.tag_configure("dim", foreground=TerminalStyle.FG_DIM)

        # Clear button
        clear_btn = tk.Button(
            log_frame,
            text="[ CLEAR ]",
            font=TerminalStyle.FONT,
            bg=TerminalStyle.BUTTON_BG,
            fg=TerminalStyle.FG_DIM,
            activebackground=TerminalStyle.FG_DIM,
            activeforeground=TerminalStyle.BG,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_log,
            padx=10,
            pady=2
        )
        clear_btn.pack(anchor=tk.E, pady=(5, 0))

    def style_combobox(self):
        """Apply terminal style to comboboxes"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "TCombobox",
            fieldbackground=TerminalStyle.ENTRY_BG,
            background=TerminalStyle.ENTRY_BG,
            foreground=TerminalStyle.FG,
            arrowcolor=TerminalStyle.FG,
            selectbackground=TerminalStyle.FG,
            selectforeground=TerminalStyle.BG
        )
        style.map('TCombobox',
            fieldbackground=[('readonly', TerminalStyle.ENTRY_BG)],
            selectbackground=[('readonly', TerminalStyle.FG)],
            selectforeground=[('readonly', TerminalStyle.BG)]
        )

    def build_param_fields(self):
        """Build parameter input fields based on selected task"""
        # Clear existing fields
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        self.param_entries.clear()

        task = self.task_var.get()
        params = TASK_PARAMS.get(task, {})

        if not params:
            tk.Label(
                self.params_frame,
                text="  No parameters required",
                font=TerminalStyle.FONT,
                bg=TerminalStyle.BG,
                fg=TerminalStyle.FG_DIM
            ).pack(anchor=tk.W)
            return

        for param_name, param_config in params.items():
            row_frame = tk.Frame(self.params_frame, bg=TerminalStyle.BG)
            row_frame.pack(fill=tk.X, pady=3)

            label_text = f"  {param_config['label']} >"
            tk.Label(
                row_frame,
                text=label_text,
                font=TerminalStyle.FONT,
                bg=TerminalStyle.BG,
                fg=TerminalStyle.FG_DIM,
                width=18,
                anchor=tk.W
            ).pack(side=tk.LEFT)

            entry = tk.Entry(
                row_frame,
                font=TerminalStyle.FONT,
                bg=TerminalStyle.ENTRY_BG,
                fg=TerminalStyle.ENTRY_FG,
                insertbackground=TerminalStyle.FG,
                relief=tk.FLAT,
                width=40
            )
            entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

            # Add placeholder behavior
            placeholder = param_config.get("placeholder", "")
            entry.insert(0, placeholder)
            entry.config(fg=TerminalStyle.FG_DIM)

            def on_focus_in(e, entry=entry, placeholder=placeholder):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(fg=TerminalStyle.ENTRY_FG)

            def on_focus_out(e, entry=entry, placeholder=placeholder):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(fg=TerminalStyle.FG_DIM)

            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

            self.param_entries[param_name] = (entry, placeholder)

    def on_task_change(self, event=None):
        """Handle task selection change"""
        self.build_param_fields()
        self.log(f"Task changed to: {self.task_var.get()}", tag="dim")

    def log(self, message, tag=None):
        """Add message to log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "dim")
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)

    def clear_log(self):
        """Clear log output"""
        self.log_text.delete(1.0, tk.END)

    def read_process_output(self, process, prefix, tag):
        """Read output from a process in a background thread"""
        def reader(stream, prefix, tag):
            try:
                for line in iter(stream.readline, ''):
                    if line:
                        # Schedule GUI update on main thread
                        self.root.after(0, lambda l=line.rstrip(): self.log(f"[{prefix}] {l}", tag=tag))
                    if process.poll() is not None:
                        break
            except Exception as e:
                self.root.after(0, lambda: self.log(f"[{prefix}] Stream error: {e}", tag="error"))
            finally:
                stream.close()

        # Start threads for stdout and stderr
        stdout_thread = threading.Thread(target=reader, args=(process.stdout, prefix, tag), daemon=True)
        stderr_thread = threading.Thread(target=reader, args=(process.stderr, prefix, "error"), daemon=True)
        stdout_thread.start()
        stderr_thread.start()

    def monitor_process(self, process, name, on_exit_callback):
        """Monitor a process and call callback when it exits"""
        def monitor():
            process.wait()
            self.root.after(0, on_exit_callback)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def on_api_exit(self):
        """Called when API process exits"""
        if self.api_running:
            self.api_running = False
            self.api_button.config(text="[ START API ]", fg=TerminalStyle.FG_INFO)
            exit_code = self.api_process.poll() if self.api_process else None
            if exit_code is not None and exit_code != 0:
                self.log(f"API server exited with code {exit_code}", tag="error")
            else:
                self.log("API server stopped", tag="warn")

    def on_main_exit(self):
        """Called when Main process exits"""
        if self.main_running:
            self.main_running = False
            self.main_button.config(text="[ START MAIN ]", fg=TerminalStyle.FG_WARN)
            exit_code = self.main_process.poll() if self.main_process else None
            if exit_code is not None and exit_code != 0:
                self.log(f"Main process exited with code {exit_code}", tag="error")
            else:
                self.log("Main process stopped", tag="warn")

    def toggle_api(self):
        """Start or stop fake_api.py"""
        if self.api_running:
            # Process is running, stop it
            if self.api_process and self.api_process.poll() is None:
                self.api_process.terminate()
            self.api_running = False
            self.api_button.config(text="[ START API ]", fg=TerminalStyle.FG_INFO)
            self.log("API server stopped", tag="warn")
        else:
            # Start the process
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, "fake_api.py")

            if not os.path.exists(script_path):
                self.log(f"File not found: {script_path}", tag="error")
                return

            try:
                self.api_process = subprocess.Popen(
                    [self.python_path, "-u", script_path],
                    cwd=script_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    bufsize=1
                )
                self.api_running = True
                self.api_button.config(text="[ STOP API ]", fg=TerminalStyle.FG_ERROR)
                self.log("API server started (fake_api.py)", tag="success")
                # Start reading output in background
                self.read_process_output(self.api_process, "API", "info")
                # Monitor process for unexpected exits
                self.monitor_process(self.api_process, "API", self.on_api_exit)
            except Exception as e:
                self.log(f"Failed to start API: {e}", tag="error")

    def toggle_main(self):
        """Start or stop main.py"""
        if self.main_running:
            # Process is running, stop it
            if self.main_process and self.main_process.poll() is None:
                self.main_process.terminate()
            self.main_running = False
            self.main_button.config(text="[ START MAIN ]", fg=TerminalStyle.FG_WARN)
            self.log("Main process stopped", tag="warn")
        else:
            # Start the process
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, "main.py")

            if not os.path.exists(script_path):
                self.log(f"File not found: {script_path}", tag="error")
                return

            try:
                self.main_process = subprocess.Popen(
                    [self.python_path, "-u", script_path],
                    cwd=script_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    bufsize=1
                )
                self.main_running = True
                self.main_button.config(text="[ STOP MAIN ]", fg=TerminalStyle.FG_ERROR)
                self.log("Main process started (main.py)", tag="success")
                # Start reading output in background
                self.read_process_output(self.main_process, "MAIN", "warn")
                # Monitor process for unexpected exits
                self.monitor_process(self.main_process, "MAIN", self.on_main_exit)
            except Exception as e:
                self.log(f"Failed to start main: {e}", tag="error")

    def run_task(self):
        """Send task to API"""
        platform = self.platform_var.get()
        task = self.task_var.get()

        # Collect parameters
        params = {}
        task_param_defs = TASK_PARAMS.get(task, {})

        for param_name, (entry, placeholder) in self.param_entries.items():
            value = entry.get()
            # Skip if value is placeholder or empty
            if value and value != placeholder:
                params[param_name] = value

        # Validate required params
        missing = []
        for param_name in task_param_defs:
            if param_name not in params or not params[param_name]:
                missing.append(param_name)

        if missing:
            self.log(f"Missing required parameters: {', '.join(missing)}", tag="error")
            return

        # Build task payload
        task_payload = {
            "platform": platform,
            "task": task,
            "enabled": True,
            "params": params
        }

        self.log("-" * 40)
        self.log(f"Sending task: {platform}.{task}", tag="info")
        self.log(f"Params: {json.dumps(params, indent=2)}", tag="dim")

        # Send to API
        try:
            url = f"{self.api_endpoint}/tasks"
            data = json.dumps(task_payload).encode('utf-8')

            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode())
                self.log(f"Task queued successfully!", tag="success")
                self.log(f"Response: {result}", tag="dim")

        except urllib.error.URLError as e:
            self.log(f"Connection error: {e.reason}", tag="error")
            self.log("Is fake_api.py running? Start with: python fake_api.py", tag="warn")
        except Exception as e:
            self.log(f"Error: {e}", tag="error")

        self.log("-" * 40)


def main():
    root = tk.Tk()
    app = MedusaDevGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
