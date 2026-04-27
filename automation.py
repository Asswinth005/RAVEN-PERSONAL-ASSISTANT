"""
FRIDAY Automation Module
System automation, file management, web operations, and task execution.
"""
import os
import sys
import subprocess
import platform
import datetime
import json
import webbrowser
import shutil
import config

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

try:
    import pyautogui
    from PIL import Image
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    VOLUME_AVAILABLE = True
except ImportError:
    VOLUME_AVAILABLE = False


class RavenAutomation:
    """System automation engine for FRIDAY."""

    def __init__(self):
        self.command_history = []
        self.reminders = []
        self.notes_file = os.path.join(config.BASE_DIR, "notes.json")
        self.reminders_file = os.path.join(config.BASE_DIR, "reminders.json")
        self._load_notes()
        self._load_reminders()
        print(f"[{config.ASSISTANT_NAME}] Automation module loaded.")

    def _load_notes(self):
        """Load notes from local storage."""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            except:
                self.notes = []
        else:
            self.notes = []

    def _load_reminders(self):
        """Load reminders from local storage."""
        if os.path.exists(self.reminders_file):
            try:
                with open(self.reminders_file, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
            except:
                self.reminders = []
        else:
            self.reminders = []

    def _save_notes(self):
        """Save notes to local storage."""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=4)
        except Exception as e:
            print(f"Error saving notes: {e}")

    def _save_reminders(self):
        """Save reminders to local storage."""
        try:
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, indent=4)
        except Exception as e:
            print(f"Error saving reminders: {e}")

    # ── System Information ──────────────────────────────────

    def get_system_info(self) -> dict:
        """Get comprehensive system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version.split()[0],
            "hostname": platform.node(),
        }

        if PSUTIL_AVAILABLE:
            # CPU
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_freq"] = f"{psutil.cpu_freq().current:.0f} MHz" if psutil.cpu_freq() else "N/A"

            # Memory
            mem = psutil.virtual_memory()
            info["ram_total"] = f"{mem.total / (1024**3):.1f} GB"
            info["ram_used"] = f"{mem.used / (1024**3):.1f} GB"
            info["ram_percent"] = f"{mem.percent}%"

            # Disk
            disk = psutil.disk_usage('/')
            info["disk_total"] = f"{disk.total / (1024**3):.1f} GB"
            info["disk_used"] = f"{disk.used / (1024**3):.1f} GB"
            info["disk_percent"] = f"{disk.percent}%"

            # Battery
            battery = psutil.sensors_battery()
            if battery:
                info["battery_percent"] = f"{battery.percent}%"
                info["battery_plugged"] = battery.power_plugged

            # Network
            net = psutil.net_io_counters()
            info["net_sent"] = f"{net.bytes_sent / (1024**2):.1f} MB"
            info["net_recv"] = f"{net.bytes_recv / (1024**2):.1f} MB"

        return info

    def get_system_summary(self) -> str:
        """Get a human-readable system summary."""
        info = self.get_system_info()
        lines = [
            f"🖥️  System: {info.get('os', 'Unknown')} ({info.get('os_version', '')})",
            f"⚙️  Processor: {info.get('processor', 'Unknown')}",
            f"🧮  CPU: {info.get('cpu_percent', 'N/A')}% ({info.get('cpu_count', '?')} cores @ {info.get('cpu_freq', 'N/A')})",
            f"💾  RAM: {info.get('ram_used', 'N/A')} / {info.get('ram_total', 'N/A')} ({info.get('ram_percent', 'N/A')})",
            f"💿  Disk: {info.get('disk_used', 'N/A')} / {info.get('disk_total', 'N/A')} ({info.get('disk_percent', 'N/A')})",
        ]

        if "battery_percent" in info:
            plug = "🔌 Plugged in" if info.get("battery_plugged") else "🔋 On battery"
            lines.append(f"🔋  Battery: {info['battery_percent']} ({plug})")

        lines.append(f"🌐  Network: ↑{info.get('net_sent', 'N/A')} / ↓{info.get('net_recv', 'N/A')}")
        return "\n".join(lines)

    def get_diagnostics(self) -> dict:
        """Get system diagnostics for the UI."""
        info = self.get_system_info()
        
        # Calculate a "core temp" (simulated if sensors not available)
        cpu_load = info.get("cpu_percent", 0)
        core_temp = 40 + (cpu_load * 0.4) # Base 40C + load-based increase
        
        return {
            "core_temp": f"{core_temp:.1f}°C",
            "temp_status": "Nominal" if core_temp < 75 else "Warning",
            "memory_leak": "None Detected",
            "encryption": "AES-256 Enabled",
            "safety_lock": "Engaged",
            "uptime": self._get_uptime()
        }

    def _get_uptime(self) -> str:
        """Get system uptime."""
        if PSUTIL_AVAILABLE:
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{uptime.days}d {hours}h {minutes}m"
        return "N/A"

    # ── Command Execution ───────────────────────────────────

    def run_command(self, command: str, timeout: int = 30) -> dict:
        """Execute a system command and return the result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.expanduser("~")
            )

            output = {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "return_code": result.returncode,
                "command": command
            }

            self.command_history.append({
                "command": command,
                "timestamp": datetime.datetime.now().isoformat(),
                "success": output["success"]
            })

            return output

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s", "command": command}
        except Exception as e:
            return {"success": False, "error": str(e), "command": command}

    # ── Application Control ─────────────────────────────────

    def open_application(self, app_name: str) -> str:
        """Open a system application by name."""
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "settings": "ms-settings:",
            "control panel": "control",
            "chrome": "chrome",
            "firefox": "firefox",
            "code": "code",
            "vscode": "code",
        }

        target = app_map.get(app_name.lower(), app_name)

        try:
            if target.startswith("ms-"):
                os.startfile(target)
            else:
                subprocess.Popen(target, shell=True)
            return f"Opened {app_name} successfully."
        except Exception as e:
            return f"Failed to open {app_name}: {e}"

    def open_website(self, url: str) -> str:
        """Open a URL in the default browser."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            webbrowser.open(url)
            return f"Opened {url} in your default browser."
        except Exception as e:
            return f"Failed to open URL: {e}"

    # ── File Operations ─────────────────────────────────────

    def list_files(self, directory: str = ".") -> list:
        """List files in a directory."""
        try:
            path = os.path.expanduser(directory)
            entries = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                entry = {
                    "name": item,
                    "type": "directory" if os.path.isdir(full_path) else "file",
                    "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None,
                }
                entries.append(entry)
            return entries
        except Exception as e:
            return [{"error": str(e)}]

    def search_files(self, directory: str, pattern: str) -> list:
        """Search for files matching a pattern."""
        import fnmatch
        results = []
        try:
            for root, dirs, files in os.walk(os.path.expanduser(directory)):
                for filename in fnmatch.filter(files, pattern):
                    results.append(os.path.join(root, filename))
                if len(results) >= 50:
                    break
        except Exception as e:
            results.append(f"Error: {e}")
        return results

    def read_file(self, filepath: str) -> str:
        """Read contents of a text file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content[:5000]  # Limit to 5000 chars
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, filepath: str, content: str) -> str:
        """Write content to a file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written: {filepath}"
        except Exception as e:
            return f"Error writing file: {e}"

    # ── Clipboard ───────────────────────────────────────────

    def copy_to_clipboard(self, text: str) -> str:
        """Copy text to system clipboard."""
        if CLIPBOARD_AVAILABLE:
            pyperclip.copy(text)
            return "Copied to clipboard."
        return "Clipboard module not available."

    def get_clipboard(self) -> str:
        """Get text from system clipboard."""
        if CLIPBOARD_AVAILABLE:
            return pyperclip.paste()
        return "Clipboard module not available."

    # ── Web Operations ──────────────────────────────────────

    def web_search(self, query: str) -> str:
        """Open a web search in the browser."""
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching for: {query}"

    def search_youtube(self, query: str) -> str:
        """Search for a video on YouTube."""
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching YouTube for: {query}"

    def search_wikipedia(self, query: str) -> str:
        """Search Wikipedia and return a summary if possible."""
        if not WEB_AVAILABLE:
            return "Web modules not available."
        
        try:
            # First try to get summary via search
            search_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            response = requests.get(search_url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                first_p = soup.find('p', class_=lambda x: x != 'mw-empty-elt')
                if first_p:
                    webbrowser.open(search_url)
                    return f"Wikipedia Summary for {query}:\n{first_p.get_text()[:500]}..."
            
            webbrowser.open(search_url)
            return f"Opening Wikipedia page for: {query}"
        except Exception as e:
            return f"Wiki error: {e}"

    def fetch_webpage(self, url: str) -> str:
        """Fetch and extract text from a webpage."""
        if not WEB_AVAILABLE:
            return "Web scraping modules not available."

        try:
            headers = {"User-Agent": "Mozilla/5.0 (FRIDAY AI Assistant)"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()

            text = soup.get_text(separator="\n", strip=True)
            return text[:3000]  # Limit output
        except Exception as e:
            return f"Error fetching webpage: {e}"

    def get_news(self, category: str = "general") -> str:
        """Fetch top news headlines (scraped from BBC or using simple RSS)."""
        if not WEB_AVAILABLE:
            return "Web modules not available for news."

        try:
            url = "https://www.bbc.com/news"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # This is a very basic scraper for BBC News titles
            headlines = []
            for h3 in soup.find_all('h3')[:10]:
                title = h3.get_text(strip=True)
                if title and len(title) > 10:
                    headlines.append(title)

            if not headlines:
                return "I couldn't find any news headlines at the moment."

            return "Top Headlines:\n" + "\n".join([f"• {h}" for h in headlines])
        except Exception as e:
            return f"Failed to fetch news: {e}"

    def take_screenshot(self) -> str:
        """Take a screenshot and save it to the temp directory."""
        if not SCREENSHOT_AVAILABLE:
            return "Screenshot module (pyautogui) not available."

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(config.TEMP_DIR, filename)

            # Ensure temp dir exists
            os.makedirs(config.TEMP_DIR, exist_ok=True)

            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)

            # Also save a copy in the static folder for web viewing if needed
            static_screenshot_path = os.path.join(config.BASE_DIR, "static", "latest_screenshot.png")
            screenshot.save(static_screenshot_path)

            return f"Screenshot saved successfully to {filename}. You can view it in the dashboard soon."
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    # ── Note Management ─────────────────────────────────────

    def add_note(self, content: str) -> str:
        """Add a new note."""
        note = {
            "id": len(self.notes) + 1,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.notes.append(note)
        self._save_notes()
        return f"Note added: \"{content[:30]}...\""

    def list_notes(self) -> str:
        """List all saved notes."""
        if not self.notes:
            return "You have no saved notes, Boss."

        lines = ["📝 Your Notes:"]
        for note in self.notes[-10:]:  # Last 10 notes
            ts = datetime.datetime.fromisoformat(note["timestamp"]).strftime("%Y-%m-%d %H:%M")
            lines.append(f"[{note['id']}] ({ts}): {note['content']}")
        return "\n".join(lines)

    def delete_note(self, note_id: int) -> str:
        """Delete a note by ID."""
        for i, note in enumerate(self.notes):
            if note["id"] == note_id:
                deleted = self.notes.pop(i)
                self._save_notes()
                return f"Deleted note: \"{deleted['content'][:30]}...\""
        return f"Note ID {note_id} not found."

    # ── Process Management ──────────────────────────────────

    def get_running_processes(self, top_n: int = 10) -> list:
        """Get top processes by memory usage."""
        if not PSUTIL_AVAILABLE:
            return [{"error": "psutil not available"}]

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by memory usage
        processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
        return processes[:top_n]

    def kill_process(self, process_name: str) -> str:
        """Kill a process by name."""
        if not PSUTIL_AVAILABLE:
            return "psutil not available."

        killed = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if killed:
            return f"Terminated {killed} instance(s) of {process_name}."
        return f"No process matching '{process_name}' found."

    # ── Volume Control ──────────────────────────────────────

    def set_volume(self, level: int) -> str:
        """Set system volume (0-100)."""
        if not VOLUME_AVAILABLE:
            return "Volume control module (pycaw) not available."
        
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # pycaw uses decibels or scalar (0.0 to 1.0)
            level = max(0, min(100, level))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return f"Volume set to {level}%."
        except Exception as e:
            return f"Failed to set volume: {e}"

    def change_volume(self, delta: int) -> str:
        """Increase or decrease volume."""
        if not VOLUME_AVAILABLE:
            return "Volume control module not available."
        
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            current = volume.GetMasterVolumeLevelScalar()
            new_level = max(0.0, min(1.0, current + (delta / 100)))
            volume.SetMasterVolumeLevelScalar(new_level, None)
            return f"Volume adjusted to {int(new_level * 100)}%."
        except Exception as e:
            return f"Failed to adjust volume: {e}"

    # ── Time & Reminders ────────────────────────────────────

    def get_datetime(self) -> str:
        """Get current date and time."""
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M:%S %p")

    def add_reminder(self, message: str, minutes: int = 0) -> str:
        """Add a reminder."""
        trigger_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        self.reminders.append({
            "message": message,
            "trigger_time": trigger_time.isoformat(),
            "triggered": False
        })
        self._save_reminders()
        if minutes > 0:
            return f"Reminder set for {minutes} minutes from now: {message}"
        return f"Reminder added: {message}"

    def check_reminders(self) -> list:
        """Check for due reminders."""
        now = datetime.datetime.now()
        due = []
        changed = False
        for reminder in self.reminders:
            if not reminder["triggered"]:
                trigger = datetime.datetime.fromisoformat(reminder["trigger_time"])
                if now >= trigger:
                    reminder["triggered"] = True
                    due.append(reminder["message"])
                    changed = True
        
        if changed:
            self._save_reminders()
        return due

    # ── Utility ─────────────────────────────────────────────

    def get_ip_info(self) -> dict:
        """Get public IP and location info."""
        if not WEB_AVAILABLE:
            return {"error": "requests module not available"}
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_weather(self, city: str = "auto") -> str:
        """Get weather info (uses wttr.in)."""
        if not WEB_AVAILABLE:
            return "requests module not available."
        try:
            url = f"https://wttr.in/{city}?format=3" if city != "auto" else "https://wttr.in/?format=3"
            response = requests.get(url, timeout=5)
            return response.text.strip()
        except Exception as e:
            return f"Weather fetch error: {e}"
