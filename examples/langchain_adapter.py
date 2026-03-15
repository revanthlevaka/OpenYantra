"""
examples/langchain_adapter.py — OpenYantra LangChain memory backend v2.0
"""
from pathlib import Path
from typing import Any, Dict, List
from openyantra import OpenYantra

try:
    from langchain.memory.chat_memory import BaseChatMemory
except ImportError:
    raise ImportError("Install langchain: pip install langchain")

class OpenYantraChatMemory(BaseChatMemory):
    """LangChain memory backend backed by OpenYantra Chitrapat."""
    path:       str = "~/openyantra/chitrapat.ods"
    agent_name: str = "LangChain"
    memory_key: str = "chat_history"

    def _get_oy(self) -> OpenYantra:
        return OpenYantra(self.path, agent_name=self.agent_name)

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            oy = self._get_oy()
            block = oy.build_system_prompt_block()
        except FileNotFoundError:
            self._get_oy().bootstrap()
            block = self._get_oy().build_system_prompt_block()
        return {self.memory_key: block}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        oy = self._get_oy()
        try:
            oy.log_session(
                topics=[inputs.get("input","")[:80]] if inputs.get("input") else ["(turn)"],
                agent=self.agent_name,
            )
        except Exception as e:
            print(f"[OpenYantra LangChain] Could not save context: {e}")

    def clear(self) -> None:
        print("[OpenYantra] clear() called but Chitrapat is persistent. "
              "Edit the .ods file directly to clear data.")
