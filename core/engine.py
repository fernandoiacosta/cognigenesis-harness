from __future__ import annotations

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
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.policy = policy
        self.context_compiler = context_compiler
        self.state = state
        self.max_steps = max_steps

    def run(self, objective: str) -> str:
        history: list[dict] = []
        self.state.set_objective(objective)

        for step in range(1, self.max_steps + 1):
            context = self.context_compiler.compile(objective, history)
            response = self.provider.generate(context)

            if response.final is not None:
                self.state.record_event("final", {"step": step, "text": response.final})
                return response.final

            if not response.tool_calls:
                gap = "CAPABILITY_GAP: model returned neither a final answer nor an executable tool call"
                self.state.record_event("capability_gap", {"step": step, "reason": gap})
                return gap

            for call in response.tool_calls:
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

                history.append({"tool_call": call.name, "arguments": call.arguments, "observation": observation})
                self.state.record_event("tool_observation", observation)

        result = f"Stopped after max_steps={self.max_steps} without a final answer."
        self.state.record_event("max_steps", {"reason": result})
        return result
