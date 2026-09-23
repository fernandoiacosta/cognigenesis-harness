"""API-key based cloud model adapters. Subscription OAuth is not an API credential."""
from __future__ import annotations

import json
import os
import keyring
from dataclasses import dataclass
from urllib import request, error

from core.types import ModelResponse, ToolCall
from providers.base import ModelProvider, ProviderError
from providers.ollama import OllamaProvider

ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "grok": "https://api.x.ai/v1/chat/completions",
}
ENV_KEYS = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GEMINI_API_KEY", "grok": "XAI_API_KEY", "meta": "COGNI_META_API_KEY"}
DEFAULT_MODELS = {"openai": "gpt-4.1-mini", "anthropic": "claude-sonnet-4-5", "google": "gemini-2.5-flash", "grok": "grok-3-mini", "meta": ""}


def _post(url: str, payload: dict, headers: dict, timeout: float) -> dict:
    req = request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", "replace")
        raise ProviderError(f"Provider HTTP {exc.code}: {detail}") from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise ProviderError(f"Provider connection failed: {exc}") from exc
    except (ValueError, KeyError) as exc:
        raise ProviderError("Provider returned an invalid response") from exc


def _calls(items):
    result = []
    for item in items:
        fn = item.get("function", item)
        arguments = fn.get("arguments", fn.get("input", {}))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError:
                arguments = {"input": arguments}
        result.append(ToolCall(name=fn["name"], arguments=arguments))
    return result


@dataclass
class CloudProvider(ModelProvider):
    name: str
    model: str
    base_url: str | None = None
    timeout: float = 120

    def generate(self, context: dict) -> ModelResponse:
        key = os.environ.get(ENV_KEYS[self.name]) or keyring.get_password("cognigenesis-harness", self.name)
        if not key:
            raise ProviderError(f"Missing {ENV_KEYS[self.name]}. Run: cogni login {self.name}")
        messages = OllamaProvider()._messages(context)
        # The runtime does not retain vendor tool IDs; flatten previous tool
        # calls/results into text to keep the next request valid.
        messages = [{"role": "assistant", "content": json.dumps(m.get("tool_calls"), ensure_ascii=False)} if m.get("tool_calls") else {"role": "user", "content": m["content"]} if m["role"] == "tool" else m for m in messages]
        tools = OllamaProvider()._tools(context)
        if self.name in {"openai", "grok", "meta"}:
            endpoint = self.base_url or ENDPOINTS.get(self.name)
            if not endpoint:
                raise ProviderError("Meta requires an OpenAI-compatible endpoint: cogni login meta --base-url URL")
            body = _post(endpoint, {"model": self.model, "messages": messages, **({"tools": tools} if tools else {})}, {"Authorization": f"Bearer {key}"}, self.timeout)
            message = body["choices"][0]["message"]
            calls = _calls(message.get("tool_calls") or [])
            return ModelResponse(tool_calls=calls) if calls else ModelResponse(final=message.get("content") or "")
        if self.name == "anthropic":
            system = messages[0]["content"]
            conversation = []
            for item in messages[1:]:
                if item["role"] == "tool":
                    conversation.append({"role": "user", "content": str(item["content"])})
                elif item["role"] == "assistant" and item.get("tool_calls"):
                    conversation.append({"role": "assistant", "content": [{"type": "tool_use", "id": t.get("id", "tool"), "name": t["function"]["name"], "input": t["function"].get("arguments", {})} for t in item["tool_calls"]]})
                else:
                    conversation.append(item)
            native_tools = [{"name": t["function"]["name"], "description": t["function"]["description"], "input_schema": t["function"]["parameters"]} for t in tools]
            body = _post(self.base_url or "https://api.anthropic.com/v1/messages", {"model": self.model, "max_tokens": 4096, "system": system, "messages": conversation, **({"tools": native_tools} if native_tools else {})}, {"x-api-key": key, "anthropic-version": "2023-06-01"}, self.timeout)
            calls = [ToolCall(name=b["name"], arguments=b.get("input", {})) for b in body.get("content", []) if b.get("type") == "tool_use"]
            return ModelResponse(tool_calls=calls) if calls else ModelResponse(final="\n".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"))
        # Gemini REST API uses function declarations and functionResponse parts.
        contents = []
        for item in messages[1:]:
            if item["role"] == "tool":
                contents.append({"role": "user", "parts": [{"text": str(item["content"])}]})
            elif item["role"] == "assistant" and item.get("tool_calls"):
                contents.append({"role": "model", "parts": [{"functionCall": {"name": t["function"]["name"], "args": t["function"].get("arguments", {})}} for t in item["tool_calls"]]})
            else:
                contents.append({"role": "model" if item["role"] == "assistant" else "user", "parts": [{"text": item.get("content", "")}]})
        declarations = [{"name": t["function"]["name"], "description": t["function"]["description"], "parameters": t["function"]["parameters"]} for t in tools]
        endpoint = self.base_url or f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = _post(endpoint, {"systemInstruction": {"parts": [{"text": messages[0]["content"]}]}, "contents": contents, **({"tools": [{"functionDeclarations": declarations}]} if declarations else {})}, {"x-goog-api-key": key}, self.timeout)
        parts = body["candidates"][0]["content"]["parts"]
        calls = [ToolCall(name=p["functionCall"]["name"], arguments=p["functionCall"].get("args", {})) for p in parts if "functionCall" in p]
        return ModelResponse(tool_calls=calls) if calls else ModelResponse(final="\n".join(p.get("text", "") for p in parts))


@dataclass
class LocalOpenAIProvider(ModelProvider):
    name: str
    model: str
    base_url: str
    timeout: float = 120

    def generate(self, context: dict) -> ModelResponse:
        messages = OllamaProvider()._messages(context)
        # Many small on-device models and local servers do not support function calling.
        body = _post(self.base_url.rstrip("/") + "/v1/chat/completions", {"model": self.model, "messages": messages}, {}, self.timeout)
        return ModelResponse(final=body["choices"][0]["message"].get("content") or "")
