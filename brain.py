"""
FRIDAY Brain Module
Core AI engine — handles conversation, reasoning, and response generation.
Uses Groq (primary) with OpenAI fallback.
"""
import datetime
import json
import traceback
from groq import Groq
from openai import OpenAI
import config


class RavenBrain:
    """The AI reasoning core of FRIDAY."""

    def __init__(self):
        self.conversation_history = []
        self.groq_client = None
        self.openai_client = None
        self._init_clients()
        self._init_conversation()

    def _init_clients(self):
        """Initialize API clients."""
        if config.GROQ_API_KEY and config.GROQ_API_KEY != "your_groq_api_key_here":
            self.groq_client = Groq(api_key=config.GROQ_API_KEY)
            print(f"[{config.ASSISTANT_NAME}] Groq client initialized (primary)")

        if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here":
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            print(f"[{config.ASSISTANT_NAME}] OpenAI client initialized (fallback)")

        if not self.groq_client and not self.openai_client:
            print(f"[{config.ASSISTANT_NAME}] WARNING: No API keys configured. Running in offline mode.")

    def _init_conversation(self):
        """Set up the initial conversation with system prompt."""
        self.conversation_history = [
            {"role": "system", "content": config.SYSTEM_PROMPT}
        ]

    def _get_time_context(self):
        """Get current time context for the AI."""
        now = datetime.datetime.now()
        return f"\n[System Time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}]"

    def think(self, user_input: str, system_context: str = "") -> str:
        """
        Process user input and generate a response.

        Args:
            user_input: The user's message
            system_context: Optional system context (e.g., automation results)

        Returns:
            FRIDAY's response string
        """
        # Build the message with time context
        message_content = user_input + self._get_time_context()
        if system_context:
            message_content += f"\n[System Context: {system_context}]"

        self.conversation_history.append({
            "role": "user",
            "content": message_content
        })

        # Keep conversation history manageable (last 20 exchanges)
        if len(self.conversation_history) > 41:  # system + 20 pairs
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-40:]

        response = self._call_ai()

        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    def _call_ai(self) -> str:
        """Call the AI API (Groq primary, OpenAI fallback, offline last resort)."""
        # Try Groq first
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=config.GROQ_CHAT_MODEL,
                    messages=self.conversation_history,
                    temperature=0.7,
                    max_tokens=2048,
                    timeout=15.0, # Added timeout
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[{config.ASSISTANT_NAME}] Groq error: {e}")

        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=config.OPENAI_CHAT_MODEL,
                    messages=self.conversation_history,
                    temperature=0.7,
                    max_tokens=2048,
                    timeout=15.0, # Added timeout
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[{config.ASSISTANT_NAME}] OpenAI error: {e}")

        # Offline fallback
        return self._offline_response()

    def _offline_response(self) -> str:
        """Generate a basic offline response when no API is available."""
        return (
            f"I'm currently running in offline mode, {config.BOSS_NAME}. "
            f"My AI core needs an API key to function at full capacity. "
            f"Please configure your Groq or OpenAI API key in the .env file. "
            f"I can still handle basic system automation in the meantime."
        )

    def reset_conversation(self):
        """Clear conversation history and start fresh."""
        self._init_conversation()
        return f"Memory cleared, {config.BOSS_NAME}. Starting fresh."

    def get_conversation_summary(self) -> dict:
        """Get a summary of the current conversation state."""
        user_msgs = [m for m in self.conversation_history if m["role"] == "user"]
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": len(user_msgs),
            "assistant_messages": len(self.conversation_history) - len(user_msgs) - 1,
        }
