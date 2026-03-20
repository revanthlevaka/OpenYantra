"""
examples/langchain_adapter.py -- LangChain memory backend v2.2
"""
from pathlib import Path
from typing import Any, Dict, List
from openyantra import OpenYantra

try:
    from langchain.memory.chat_memory import BaseChatMemory
except ImportError:
    raise ImportError("pip install langchain")

class OpenYantraChatMemory(BaseChatMemory):
    path: str = "~/openyantra/chitrapat.ods"
    agent_name: str = "LangChain"
    memory_key: str = "chat_history"

    def _get_oy(self) -> OpenYantra:
        return OpenYantra(self.path, agent_name=self.agent_name)

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        oy = self._get_oy()
        if not Path(self.path).expanduser().exists():
            oy.bootstrap()
        return {self.memory_key: oy.build_system_prompt_block()}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        oy = self._get_oy()
        oy.log_session(topics=[inputs.get("input", "")[:80]] or ["(turn)"])

    def clear(self) -> None:
        print("[OpenYantra] Chitrapat is persistent. Edit .ods directly to clear.")
