"""
examples/langchain_adapter.py — UAM integration for LangChain agents

Wraps OpenYantra as a LangChain BaseChatMemory so any LangChain
agent can use UAM as its persistent memory backend.

Requirements:
    pip install langchain openpyxl
"""

from pathlib import Path
from typing import Any, Dict, List

from openyantra import OpenYantra

try:
    from langchain.memory.chat_memory import BaseChatMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
except ImportError:
    raise ImportError("Install langchain: pip install langchain")


class OpenYantraChatMemory(BaseChatMemory):
    """
    LangChain memory backend backed by a UAM .xlsx file.

    Usage:
        from uam.examples.langchain_adapter import OpenYantraChatMemory
        from langchain.agents import initialize_agent

        memory = OpenYantraChatMemory(uam_path="~/uam/memory.xlsx", agent_name="MyAgent")
        agent = initialize_agent(tools, llm, memory=memory, ...)
    """

    uam_path: str = "~/uam/memory.xlsx"
    agent_name: str = "LangChain"
    memory_key: str = "chat_history"

    @property
    def _mem(self) -> OpenYantra:
        return OpenYantra(self.uam_path, agent_name=self.agent_name)

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load UAM context and inject as chat history prefix."""
        try:
            block = self._mem.build_system_prompt_block(self.agent_name)
        except FileNotFoundError:
            self._mem.bootstrap()
            block = self._mem.build_system_prompt_block(self.agent_name)

        return {self.memory_key: block}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Called after each agent turn.
        Extract any facts from the exchange and persist them.
        """
        # Minimal implementation: log the session at each save.
        # In production: parse inputs/outputs for new facts, open loops, etc.
        user_input = inputs.get("input", "")
        agent_output = outputs.get("output", "")

        try:
            self._mem.log_session(
                topics=[user_input[:80]] if user_input else ["(turn)"],
                agent=self.agent_name,
            )
        except Exception as e:
            print(f"[UAM LangChain] Could not save context: {e}")

    def clear(self) -> None:
        """Does not clear UAM — memory is persistent by design."""
        print("[UAM LangChain] clear() called but UAM memory is persistent. Use the xlsx file to edit directly.")
