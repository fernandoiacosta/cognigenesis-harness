from __future__ import annotations

from threading import Event

from core.context import ContextCompiler
from core.policy import Policy
from core.registry import CapabilityRegistry
from providers.base import ModelProvider
from state.store import StateStore


class ExecutionEngine:
    def __init__(
        self,
        provider: ModelProvider,
        registry: CapabilityRegistry,
        policy: Policy,
        context_compiler: ContextCompiler,
        state: StateStore,
        max_steps: int = 12,
        cancel_event: Event | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.policy = policy
        self.context_compiler = context_compiler
        self.state = state
        self.max_steps = max_steps
        self.cancel_event = cancel_event
        self.history: list[dict] = self.state.conversation()[-80:]

    def _is_cancelled(self) -> bool:
        return bool(self.cancel_event and self.cancel_event.is_set())

    def _cancelled_result(self, step: int | None = None) -> str:
        payload: dict[str, int | str] = {"reason": "Execution cancelled by client."}
        if step is not None:
            payload["step"] = step
        self.state.record_event("cancelled", payload)
        return "Execution cancelled by client."

    def reset_conversation(self) -> None:
        self.history.clear()
        self.state.set_conversation([])
        self.state.record_event("conversation_reset", {})

    def conversation_history(self) -> list[dict]:
        return list(self.history)

    def _persist_history(self) -> None:
        self.history = self.history[-80:]
        self.state.set_conversation(self.history)

    def _commit_turn(self, objective: str, turn_items: list[dict], assistant_text: str) -> None:
        self.history.append({"role": "user", "content": objective})
        self.history.extend(turn_items)
        self.history.append({"role": "assistant", "content": assistant_text})
        self._persist_history()

    def run(self, objective: str) -> str:
        self.state.set_objective(objective)
        turn_items: list[dict] = []

        if self._is_cancelled():
            return self._cancelled_result()

        for step in range(1, self.max_steps + 1):
            if self._is_cancelled():
                return self._cancelled_result(step)

            working_history = self.history + [{"role": "user", "content": objective, "current_turn": True}] + turn_items
            context = self.context_compiler.compile(objective, working_history)
            context["objective_in_history"] = True
            response = self.provider.generate(context)

            if self._is_cancelled():
                return self._cancelled_result(step)

            if response.final is not None:
                self._commit_turn(objective, turn_items, response.final)
                self.state.record_event("final", {"step": step, "text": response.final})
                return response.final

            if not response.tool_calls:
                gap = "CAPABILITY_GAP: model returned neither a final answer nor an executable tool call"
                self._commit_turn(objective, turn_items, gap)
                self.state.record_event("capability_gap", {"step": step, "reason": gap})
                return gap

            turn_items.append({
                "role": "assistant",
                "tool_calls": [
                    {"function": {"name": call.name, "arguments": call.arguments}}
                    for call in response.tool_calls
                ],
            })

            for call in response.tool_calls:
                if self._is_cancelled():
                    return self._cancelled_result(step)

                capability = self.registry.get(call.name)
                if capability is None:
                    observation = {
                        "ok": False,
                        "type": "CAPABILITY_GAP",
                        "capability": call.name,
                        "reason": "No trusted implementation is registered.",
                    }
                else:
                    allowed, reason = self.policy.authorize(call.name, call.arguments)
                    if not allowed:
                        observation = {
                            "ok": False,
                            "type": "POLICY_DENIED",
                            "capability": call.name,
                            "reason": reason,
                        }
                    else:
                        try:
                            result = capability.execute(call.arguments)
                            observation = {"ok": True, "capability": call.name, "result": result}
                        except Exception as exc:
                            observation = {
                                "ok": False,
                                "type": "TOOL_ERROR",
                                "capability": call.name,
                                "reason": str(exc),
                            }

                turn_items.append({
                    "role": "tool",
                    "name": call.name,
                    "content": observation,
                })
                self.state.record_event("tool_observation", observation)

        result = f"Stopped after max_steps={self.max_steps} without a final answer."
        self._commit_turn(objective, turn_items, result)
        self.state.record_event("max_steps", {"reason": result})
        return result
