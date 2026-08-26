from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from urllib import error, request

from core.types import ModelResponse, ToolCall
from providers.base import ModelProvider, ProviderError


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_TIMEOUT = 120.0


@dataclass
class OllamaProvider(ModelProvider):
    model: str = DEFAULT_OLLAMA_MODEL
    base_url: str = DEFAULT_OLLAMA_BASE_URL
    timeout: float = DEFAULT_OLLAMA_TIMEOUT

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")

    def generate(self, context: dict) -> ModelResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": self._messages(context),
            "tools": self._tools(context),
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 404 or "model" in detail.lower() and "not found" in detail.lower():
                raise ProviderError(
                    f"Ollama model '{self.model}' is not available. Run: ollama pull {self.model}"
                ) from exc
            raise ProviderError(
                f"Ollama returned HTTP {exc.code} from {self.base_url}: {detail or exc.reason}"
            ) from exc
        except (error.URLError, ConnectionError, socket.timeout, TimeoutError, OSError) as exc:
            raise ProviderError(
                f"Ollama is not reachable at {self.base_url}. Start Ollama and verify it with: ollama list"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("Ollama returned an invalid JSON response.") from exc

        if body.get("error"):
            message = str(body["error"])
            if "model" in message.lower() and ("not found" in message.lower() or "pull" in message.lower()):
                raise ProviderError(
                    f"Ollama model '{self.model}' is not available. Run: ollama pull {self.model}"
                )
            raise ProviderError(f"Ollama error: {message}")

        message = body.get("message") or {}
        calls: list[ToolCall] = []
        for item in message.get("tool_calls") or []:
            function = item.get("function") or {}
            name = function.get("name")
            arguments = function.get("arguments") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"input": arguments}
            if name:
                calls.append(ToolCall(name=name, arguments=arguments))

        content = (message.get("content") or "").strip()
        if calls:
            return ModelResponse(tool_calls=calls)
        if not content:
            raise ProviderError("Ollama returned neither text nor tool calls.")
        return ModelResponse(final=content)

    def _messages(self, context: dict) -> list[dict]:
        system = context.get("system", "")
        capabilities = context.get("capabilities", [])
        state = context.get("state", {})
        system_suffix = (
            "\n\nRuntime capabilities:\n"
            + "\n".join(f"- {c['id']}: {c['description']}" for c in capabilities)
            + "\n\nCurrent runtime state:\n"
            + json.dumps(state, ensure_ascii=False)
        )
        messages: list[dict] = [{"role": "system", "content": system + system_suffix}]

        for item in context.get("history", []):
            role = item.get("role")
            if role in {"user", "assistant"} and isinstance(item.get("content"), str):
                messages.append({"role": role, "content": item["content"]})
            elif role == "tool" or "observation" in item:
                messages.append({
                    "role": "tool",
                    "content": json.dumps(item.get("observation", item), ensure_ascii=False),
                })

        messages.append({"role": "user", "content": context.get("objective", "")})
        return messages

    def _tools(self, context: dict) -> list[dict]:
        tools = []
        for capability in context.get("capabilities", []):
            tools.append({
                "type": "function",
                "function": {
                    "name": capability["id"],
                    "description": capability["description"],
                    "parameters": {
                        "type": "object",
                        "additionalProperties": True,
                    },
                },
            })
        return tools
