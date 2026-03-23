"""
CyberMind AI - Local AI Agent
Powered by Ollama - 100% offline, no API keys needed
"""
import json
import re
from typing import List, Dict, Optional, Callable
from config import config
from utils.logger import get_logger

logger = get_logger("ai_agent")


class AIAgent:
    """
    Local AI agent powered by Ollama.
    Supports streaming, tool use via ReAct prompting, and RAG.
    """

    # ReAct-style tool calling prompt
    TOOL_SYSTEM_ADDON = """
You have access to the following tools. To use a tool, respond with:
<tool_call>
{"name": "tool_name", "arguments": {"param": "value"}}
</tool_call>

After getting a tool result, continue your analysis.
Available tools:
- run_python: Execute Python code (crypto, encoding, analysis scripts)
- web_request: Make HTTP requests to web targets
- analyze_text: Analyze text for encoding/cipher hints
- decode_data: Decode base64/hex/rot13/binary data
- search_knowledge: Search CTF writeups knowledge base

Always explain what you're doing and why before using a tool.
"""

    def __init__(self, rag_engine=None, tool_executor=None):
        self._client = None
        self.rag_engine = rag_engine
        self.tool_executor = tool_executor
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the Ollama client"""
        try:
            import ollama
            self._client = ollama.Client(host=config.OLLAMA_HOST)
            # Test connection
            self._client.list()
            self._initialized = True
            logger.info(f"AI Agent initialized with local model: {config.AI_MODEL}")
            return True
        except ImportError:
            logger.error("ollama package not installed. Run: pip install ollama")
            return False
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}")
            return False

    def is_ready(self) -> bool:
        return self._initialized

    def chat(
        self,
        messages: List[Dict],
        system_prompt: str,
        on_text: Optional[Callable[[str], None]] = None,
        on_tool_start: Optional[Callable[[str, Dict], None]] = None,
        on_tool_end: Optional[Callable[[str, Dict], None]] = None,
        on_done: Optional[Callable[[str], None]] = None,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> str:
        """
        Send messages to local Ollama model with streaming + RAG + tool use.
        """
        if not self._initialized:
            msg = "⚠️ Ollama not running. Start it with: ollama serve"
            if on_text:
                on_text(msg)
            if on_done:
                on_done(msg)
            return msg

        # Inject RAG context
        enhanced_system = system_prompt
        if use_rag and self.rag_engine and self.rag_engine.is_ready():
            last_user = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"),
                ""
            )
            if last_user:
                context = self.rag_engine.get_context_for_query(last_user)
                if context:
                    enhanced_system = f"{system_prompt}\n\n{context}"

        # Add tool instructions
        if use_tools:
            enhanced_system += self.TOOL_SYSTEM_ADDON

        # Build Ollama messages
        ollama_messages = [{"role": "system", "content": enhanced_system}]
        ollama_messages.extend(messages)

        full_response = ""
        max_iterations = 6

        for iteration in range(max_iterations):
            chunk_buffer = ""

            try:
                import ollama as ollama_lib
                stream = self._client.chat(
                    model=config.AI_MODEL,
                    messages=ollama_messages,
                    stream=True,
                    options={
                        "temperature": config.AI_TEMPERATURE,
                        "num_predict": config.AI_MAX_TOKENS,
                    }
                )

                for chunk in stream:
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        chunk_buffer += delta
                        full_response += delta
                        if on_text:
                            on_text(delta)

            except Exception as e:
                error_msg = f"\n\n❌ Ollama error: {str(e)}"
                if on_text:
                    on_text(error_msg)
                full_response += error_msg
                logger.error(f"Ollama error: {e}")
                break

            # Check for tool calls in the response
            tool_calls = self._extract_tool_calls(chunk_buffer)

            if not tool_calls or not use_tools or not self.tool_executor:
                break

            # Execute each tool call
            tool_results_text = ""
            for tool_name, tool_args in tool_calls:
                if on_tool_start:
                    on_tool_start(tool_name, tool_args)

                result = self.tool_executor.execute(tool_name, tool_args)
                result_text = self.tool_executor.format_result(tool_name, result)

                if on_tool_end:
                    on_tool_end(tool_name, result)

                tool_result_msg = f"\n\n**[Tool: {tool_name}]**\n```\n{result_text}\n```\n\n"
                tool_results_text += tool_result_msg

                if on_text:
                    on_text(tool_result_msg)

                full_response += tool_result_msg

            # Add assistant response and tool results to history
            ollama_messages.append({"role": "assistant", "content": chunk_buffer})
            ollama_messages.append({
                "role": "user",
                "content": f"Tool results:\n{tool_results_text}\n\nPlease continue your analysis."
            })

        if on_done:
            on_done(full_response)

        return full_response

    def _extract_tool_calls(self, text: str) -> List[tuple]:
        """Extract tool calls from model output"""
        calls = []
        pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                name = data.get("name", "")
                args = data.get("arguments", {})
                if name:
                    calls.append((name, args))
            except json.JSONDecodeError:
                pass

        return calls

    def quick_analyze(self, text: str, context: str = "") -> str:
        """Quick non-streaming response — uses RAG knowledge base if available"""
        if not self._initialized:
            return "Agent not initialized"
        try:
            system = f"You are CyberMind, a senior penetration tester and CTF expert. {context}"

            # Inject RAG context from training data
            if self.rag_engine and self.rag_engine.is_ready():
                rag_context = self.rag_engine.get_context_for_query(text)
                if rag_context:
                    system = f"{system}\n\n{rag_context}"

            response = self._client.chat(
                model=config.AI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text}
                ],
                options={"temperature": 0.3, "num_predict": 4096}
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Error: {e}"

    def pull_model(self, model_name: str,
                   on_progress: Optional[Callable[[str], None]] = None) -> bool:
        """Download a model via Ollama"""
        try:
            import ollama as ollama_lib
            if on_progress:
                on_progress(f"Downloading {model_name}...")

            for progress in self._client.pull(model_name, stream=True):
                status = progress.get("status", "")
                completed = progress.get("completed", 0)
                total = progress.get("total", 0)

                if on_progress and total > 0:
                    pct = completed / total * 100
                    on_progress(f"Downloading {model_name}: {pct:.1f}%")
                elif on_progress and status:
                    on_progress(f"{model_name}: {status}")

            if on_progress:
                on_progress(f"✅ {model_name} ready!")
            return True

        except Exception as e:
            if on_progress:
                on_progress(f"❌ Failed: {e}")
            return False
