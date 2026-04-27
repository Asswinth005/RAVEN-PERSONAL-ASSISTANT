"""
FRIDAY -- Main Entry Point
Launch FRIDAY in Web GUI mode or CLI mode.
"""
import sys
import os
import argparse

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.system("")  # Enable ANSI escape codes on Windows
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import config


def print_banner():
    """Display the FRIDAY startup banner."""
    banner = """
\033[96m
    +====================================================+
    |                                                      |
    |     RRRR    AAA   V   V  EEEEE  N   N                |
    |     R   R  A   A  V   V  E      NN  N                |
    |     RRRR   AAAAA  V   V  EEEE   N N N                |
    |     R  R   A   A   V V   E      N  NN                |
    |     R   R  A   A    V    EEEEE  N   N                |
    |                                                      |
    |        Advanced AI Assistant System v3.1              |
    +====================================================+
\033[0m"""
    print(banner)


def run_cli():
    """Run FRIDAY in CLI (terminal) mode."""
    from brain import RavenBrain
    from automation import RavenAutomation
    from router import CommandRouter

    brain = RavenBrain()
    automation = RavenAutomation()
    router = CommandRouter(automation)

    # Optional voice
    voice = None
    try:
        from voice import RavenVoice
        voice = RavenVoice()
        voice.speak(f"{config.ASSISTANT_NAME} online. All systems operational, {config.BOSS_NAME}.")
    except Exception as e:
        print(f"[{config.ASSISTANT_NAME}] Voice disabled: {e}")

    print(f"\n\033[96m[{config.ASSISTANT_NAME}]\033[0m Ready. Type your commands or say 'exit' to quit.")
    print(f"\033[90mTip: Type 'voice' to use voice input | 'help' for commands\033[0m\n")

    while True:
        try:
            user_input = input(f"\033[93m{config.BOSS_NAME} ▸ \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\033[96m[{config.ASSISTANT_NAME}]\033[0m Shutting down. Goodbye, {config.BOSS_NAME}.")
            break

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit', 'bye', 'shutdown']:
            print(f"\033[96m[{config.ASSISTANT_NAME}]\033[0m All systems offline. Until next time, {config.BOSS_NAME}.")
            if voice:
                voice.speak(f"All systems offline. Until next time, {config.BOSS_NAME}.")
                voice.shutdown()
            break

        if user_input.lower() == 'voice':
            if voice:
                text = voice.listen()
                if text:
                    user_input = text
                    print(f"\033[92m🎤 Heard:\033[0m {text}")
                else:
                    print(f"\033[96m[{config.ASSISTANT_NAME}]\033[0m Didn't catch that. Try again?")
                    continue
            else:
                print(f"\033[96m[{config.ASSISTANT_NAME}]\033[0m Voice module not available.")
                continue

        if user_input.lower() == 'help':
            print_help()
            continue

        # Try routing to automation
        handled, result = router.try_route(user_input)

        if handled:
            if result == "__RESET__":
                result = brain.reset_conversation()

            print(f"\033[96m[{config.ASSISTANT_NAME}]\033[0m {result}")

            # Also get AI commentary
            if len(result) > 20:
                ai_response = brain.think(user_input, system_context=f"Automation result: {result[:300]}")
                print(f"\033[96m[{config.ASSISTANT_NAME}]\033[0m 💬 {ai_response}")
                if voice:
                    voice.speak(ai_response.split('\n')[0][:150])
        else:
            # Pure AI
            response = brain.think(user_input)
            print(f"\033[96m[{config.ASSISTANT_NAME}]\033[0m {response}")
            if voice:
                voice.speak(response.split('\n')[0][:150])

        # Check reminders
        due_reminders = automation.check_reminders()
        for reminder in due_reminders:
            print(f"\033[93m[⏰ REMINDER]\033[0m {reminder}")
            if voice:
                voice.speak(f"Reminder: {reminder}")


def print_help():
    """Print available commands."""
    help_text = """
\033[96m+=====================================================+
|              FRIDAY Command Reference               |
+=====================================================+
|                                                     |
|  CONVERSATION                                       |
|    Just type naturally -- FRIDAY understands you     |
|                                                     |
|  VOICE                                              |
|    voice          -- Switch to voice input           |
|                                                     |
|  SYSTEM                                             |
|    system info    -- Show system stats               |
|    running processes -- List top processes           |
|    kill <name>    -- Terminate a process             |
|                                                     |
|  WEB                                                |
|    open <url>     -- Open a website                  |
|    search <query> -- Google search                   |
|    my ip          -- Show IP & location              |
|    weather [city] -- Get weather info                |
|                                                     |
|  FILES                                              |
|    open <app>     -- Launch an application           |
|                                                     |
|  REMINDERS                                          |
|    remind me in X min to <task>                      |
|                                                     |
|  MEMORY                                             |
|    clear memory   -- Reset conversation              |
|                                                     |
|  EXIT                                               |
|    exit / quit / bye                                 |
|                                                     |
+=====================================================+\033[0m
"""
    print(help_text)


def run_web():
    """Run FRIDAY with Web GUI."""
    from web_gui import run_web as start_web
    start_web()


def main():
    parser = argparse.ArgumentParser(description=f'{config.ASSISTANT_NAME} — Advanced AI Assistant')
    parser.add_argument('--mode', choices=['cli', 'web'], default='web',
                       help='Launch mode: cli (terminal) or web (browser GUI)')
    parser.add_argument('--port', type=int, default=config.WEB_PORT,
                       help='Port for web GUI (default: 5000)')

    args = parser.parse_args()

    print_banner()
    print(f"  Mode: {args.mode.upper()}")
    print(f"  AI: Groq ({'configured' if config.GROQ_API_KEY and config.GROQ_API_KEY != 'your_groq_api_key_here' else 'not configured'}) | OpenAI ({'configured' if config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'your_openai_api_key_here' else 'not configured'})")
    print()

    if args.mode == 'cli':
        run_cli()
    else:
        if args.port != config.WEB_PORT:
            config.WEB_PORT = args.port
        run_web()


if __name__ == '__main__':
    main()
