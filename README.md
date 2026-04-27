# 🚀 FRIDAY (Raven) AI Assistant

An advanced, Iron Man-inspired AI assistant with a real-time web dashboard, system automation, and voice capabilities.

## 🛠️ Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Install Dependencies
Open your terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Open the `.env` file and add your API keys:
- **GROQ_API_KEY**: Get it from [console.groq.com](https://console.groq.com) (Required for AI chat).
- **OPENAI_API_KEY**: (Optional) For fallback support.

## 🏃 How to Run

To launch the assistant, simply run:
```bash
python main.py
```

### Modes
- **Web Mode (Default)**: Launch the interactive dashboard.
  ```bash
  python main.py --mode web
  ```
- **CLI Mode**: Run directly in your terminal.
  ```bash
  python main.py --mode cli
  ```

## 🌐 Accessing the Dashboard
Once the script is running, open your browser and go to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

## ⌨️ Quick Commands
- **System Stats**: Click the 'System Automation' card or type "system info".
- **Voice Control**: Click the microphone icon or the 'Voice Control' card.
- **Reminders**: Type "remind me in 5 min to take a break".
- **Notes**: Type "note that the project is due tomorrow".

---
*Built with ❤️ by Raven AI Team*
