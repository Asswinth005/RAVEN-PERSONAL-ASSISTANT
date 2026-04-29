"""
FRIDAY Command Router
Parses user intent and routes to appropriate automation functions.
"""
import re
import config
from automation import RavenAutomation


class CommandRouter:
    """Routes natural language commands to automation functions."""

    def __init__(self, automation: RavenAutomation):
        self.auto = automation

    def try_route(self, user_input: str) -> tuple:
        """
        Try to route user input to an automation command.

        Returns:
            (handled: bool, result: str)
            - handled=True means a system command was executed
            - handled=False means it should go to the AI brain
        """
        text = user_input.lower().strip()

        # ── System Info ──
        if any(kw in text for kw in ["system info", "system status", "system stats",
                                       "how's my system", "cpu usage", "ram usage",
                                       "memory usage", "disk usage", "hardware"]):
            return True, self.auto.get_system_summary()

        # ── Time ──
        if any(kw in text for kw in ["what time", "current time", "what's the time",
                                       "what date", "current date", "what day"]):
            return True, f"📅 {self.auto.get_datetime()}"

        # ── Weather ──
        if "weather" in text:
            city = "auto"
            match = re.search(r"weather\s+(?:in|for|at)\s+(.+)", text)
            if match:
                city = match.group(1).strip()
            return True, f"🌤️ {self.auto.get_weather(city)}"

        # ── News ──
        if any(kw in text for kw in ["news", "headlines", "what's happening"]):
            return True, self.auto.get_news()

        # ── Screenshot ──
        if any(kw in text for kw in ["screenshot", "capture screen", "snap screen"]):
            return True, self.auto.take_screenshot()

        # ── Open Website / Application ──
        if text.startswith("open "):
            target = text.replace("open ", "").strip()
            if target.startswith("website "):
                target = target.replace("website ", "", 1)
                
            websites = {
                "youtube": "https://youtube.com",
                "google": "https://google.com",
                "facebook": "https://facebook.com",
                "twitter": "https://twitter.com",
                "x": "https://x.com",
                "reddit": "https://reddit.com",
                "github": "https://github.com",
                "chatgpt": "https://chatgpt.com",
                "gmail": "https://mail.google.com",
                "instagram": "https://instagram.com",
                "whatsapp": "https://web.whatsapp.com",
                "netflix": "https://netflix.com",
                "amazon": "https://amazon.com",
                "spotify": "https://open.spotify.com",
                "linkedin": "https://linkedin.com",
                "twitch": "https://twitch.tv",
                "discord": "https://discord.com/app",
                "pinterest": "https://pinterest.com",
                "yahoo": "https://yahoo.com",
                "bing": "https://bing.com",
            }
            
            target_spaceless = target.replace(" ", "")
            if target in websites:
                return True, self.auto.open_website(websites[target])
            elif target_spaceless in websites:
                return True, self.auto.open_website(websites[target_spaceless])
                
            if any(ext in target for ext in [".com", ".org", ".net", ".io", "http", "www"]):
                return True, self.auto.open_website(target)
                
            return True, self.auto.open_application(target)

        # ── Search ──
        if any(kw in text for kw in ["youtube", "play on youtube"]):
            query = text.replace("youtube", "").replace("play on", "").replace("search", "").strip()
            return True, self.auto.search_youtube(query)

        if "wikipedia" in text or "who is " in text or "what is " in text:
            query = text.replace("wikipedia", "").replace("who is", "").replace("what is", "").replace("search", "").strip()
            if query:
                return True, self.auto.search_wikipedia(query)

        if any(kw in text for kw in ["search for", "google ", "look up", "search "]):
            query = text
            for prefix in ["search for ", "google ", "look up ", "search "]:
                query = query.replace(prefix, "")
            return True, self.auto.web_search(query.strip())



        # ── IP Info ──
        if any(kw in text for kw in ["my ip", "ip address", "ip info", "where am i"]):
            info = self.auto.get_ip_info()
            if "error" not in info:
                return True, f"🌐 IP: {info.get('ip', 'N/A')} | Location: {info.get('city', '?')}, {info.get('region', '?')}, {info.get('country', '?')}"
            return True, f"Could not fetch IP info: {info.get('error')}"

        # ── Process List ──
        if any(kw in text for kw in ["running processes", "top processes", "process list",
                                       "what's running"]):
            procs = self.auto.get_running_processes(10)
            lines = ["📊 Top processes by memory:"]
            for p in procs:
                lines.append(f"  • {p.get('name', '?')} (PID: {p.get('pid', '?')}) — "
                           f"RAM: {p.get('memory_percent', 0):.1f}%")
            return True, "\n".join(lines)

        # ── Kill Process ──
        if text.startswith("kill ") or text.startswith("terminate "):
            proc_name = text.replace("kill ", "").replace("terminate ", "").strip()
            return True, self.auto.kill_process(proc_name)

        # ── Clipboard ──
        if any(kw in text for kw in ["clipboard", "paste", "what's copied"]):
            content = self.auto.get_clipboard()
            return True, f"📋 Clipboard: {content[:200]}"

        # ── Reminder ──
        if "remind" in text:
            match = re.search(r"remind\s+(?:me\s+)?(?:in\s+)?(\d+)\s*(?:min|minute)", text)
            minutes = int(match.group(1)) if match else 0
            msg_match = re.search(r"(?:to|about|that)\s+(.+)", text)
            message = msg_match.group(1) if msg_match else text
            return True, self.auto.add_reminder(message, minutes)

        # ── Volume ──
        if "volume" in text:
            if "set" in text or "to" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    return True, self.auto.set_volume(int(match.group(1)))
            
            if any(kw in text for kw in ["increase", "up", "louder", "raise"]):
                return True, self.auto.change_volume(10)
            
            if any(kw in text for kw in ["decrease", "down", "lower", "quieter"]):
                return True, self.auto.change_volume(-10)
            
            if "mute" in text:
                return True, self.auto.set_volume(0)

        # ── Run Command ──
        if text.startswith("run ") or text.startswith("execute "):
            cmd = text.replace("run ", "").replace("execute ", "").strip()
            result = self.auto.run_command(cmd)
            if result["success"]:
                return True, f"✅ Command executed:\n{result['stdout'][:500]}"
            else:
                error = result.get("stderr", result.get("error", "Unknown error"))
                return True, f"❌ Command failed:\n{error[:500]}"

        # ── Notes ──
        if any(kw in text for kw in ["note", "write down"]):
            if any(kw in text for kw in ["list", "show", "read"]):
                return True, self.auto.list_notes()
            
            if "delete" in text or "remove" in text:
                match = re.search(r"(?:delete|remove)\s+note\s+(\d+)", text)
                if match:
                    return True, self.auto.delete_note(int(match.group(1)))
                return True, "Please specify the note ID to delete."

            # Add note - everything after "note" or "write down"
            content = text
            for prefix in ["take a note ", "write down ", "note that ", "note "]:
                if content.startswith(prefix):
                    content = content.replace(prefix, "", 1)
                    break
            return True, self.auto.add_note(content.strip())

        # ── Clear / Reset ──
        if any(kw in text for kw in ["clear memory", "reset memory", "forget everything",
                                       "start fresh", "new conversation"]):
            return True, "__RESET__"

        # Not a direct command — let the AI brain handle it
        return False, ""
