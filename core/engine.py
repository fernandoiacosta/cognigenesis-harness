from __future__ import annotations

from threading import Event
from uuid import uuid4

from cognigenesis.cognition.ledger import CognitiveLedger
from cognigenesis.fabric.team import TeamManager
from cognigenesis.runtime.events import EventBus, EventType
from cognigenesis.runtime.taskgraph import TaskGraph
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
        *,
        event_bus: EventBus | None = None,
        task_graph: TaskGraph | None = None,
        cognition: CognitiveLedger | None = None,
        team_manager: TeamManager | None = None,
        session_id: str | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.policy = policy
        self.context_compiler = context_compiler
        self.state = state
        self.max_steps = max_steps
        self.cancel_event = cancel_event
        self.events = event_bus or EventBus()
        self.tasks = task_graph or TaskGraph()
        self.cognition = cognition or CognitiveLedger()
        self.teams = team_manager or TeamManager()
        self.session_id = session_id or uuid4().hex
        self.history: list[dict] = self.state.conversation()[-80:]

    def _emit(self, event_type: EventType, payload: dict | None = None, *, turn_id: str | None = None):
        return self.events.emit(
            event_type,
            payload or {},
            session_id=self.session_id,
            turn_id=turn_id,
            source="execution-engine",
        )

    def _is_cancelled(self) -> bool:
        return bool(self.cancel_event and self.cancel_event.is_set())

    def _cancelled_result(self, step: int | None = None, *, turn_id: str | None = None) -> str:
        payload: dict[str, int | str] = {"reason": "Execution cancelled by client."}
        if step is not None:
            payload["step"] = step
        self.state.record_event("cancelled", payload)
        self._emit(EventType.TURN_CANCELLED, payload, turn_id=turn_id)
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
        turn_id = uuid4().hex
        self._emit(EventType.TURN_STARTED, {"objective": objective}, turn_id=turn_id)

        if self._is_cancelled():
            return self._cancelled_result(turn_id=turn_id)

        for step in range(1, self.max_steps + 1):
            if self._is_cancelled():
                return self._cancelled_result(step, turn_id=turn_id)

            working_history = self.history + [{"role": "user", "content": objective, "current_turn": True}] + turn_items
            context = self.context_compiler.compile(objective, working_history)
            context["objective_in_history"] = True

            self._emit(EventType.MODEL_STARTED, {"step": step}, turn_id=turn_id)
            try:
                response = self.provider.generate(context)
            except Exception as exc:
                payload = {"step": step, "error": str(exc), "error_type": type(exc).__name__}
                self.state.record_event("model_error", payload)
                self._emit(EventType.TURN_FAILED, payload, turn_id=turn_id)
                raise
            self._emit(
                EventType.MODEL_COMPLETED,
                {"step": step, "tool_calls": len(response.tool_calls), "has_final": response.final is not None},
                turn_id=turn_id,
            )

            if self._is_cancelled():
                return self._cancelled_result(step, turn_id=turn_id)

            if response.final is not None:
                self._commit_turn(objective, turn_items, response.final)
                self.state.record_event("final", {"step": step, "text": response.final})
                self._emit(EventType.TURN_COMPLETED, {"step": step, "text": response.final}, turn_id=turn_id)
                return response.final

            if not response.tool_calls:
                gap = "CAPABILITY_GAP: model returned neither a final answer nor an executable tool call"
                self._commit_turn(objective, turn_items, gap)
                self.state.record_event("capability_gap", {"step": step, "reason": gap})
                self._emit(EventType.CAPABILITY_GAP, {"step": step, "reason": gap}, turn_id=turn_id)
                self._emit(EventType.TURN_COMPLETED, {"step": step, "text": gap}, turn_id=turn_id)
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
                    return self._cancelled_result(step, turn_id=turn_id)

                self._emit(
                    EventType.TOOL_REQUESTED,
                    {"step": step, "capability": call.name, "arguments": call.arguments},
                    turn_id=turn_id,
                )
                capability = self.registry.get(call.name)
                if capability is None:
                    observation = {
                        "ok": False,
                        "type": "CAPABILITY_GAP",
                        "capability": call.name,
                        "reason": "No trusted implementation is registered.",
                    }
                    self._emit(EventType.CAPABILITY_GAP, observation, turn_id=turn_id)
                else:
                    allowed, reason = self.policy.authorize(call.name, call.arguments)
                    if not allowed:
                        observation = {
                            "ok": False,
                            "type": "POLICY_DENIED",
                            "capability": call.name,
                            "reason": reason,
                        }
                        self._emit(EventType.POLICY_DENIED, observation, turn_id=turn_id)
                    else:
                        self._emit(
                            EventType.TOOL_STARTED,
                            {"step": step, "capability": call.name},
                            turn_id=turn_id,
                        )
                        try:
                            result = capability.execute(call.arguments)
                            observation = {"ok": True, "capability": call.name, "result": result}
                            self._emit(EventType.TOOL_COMPLETED, observation, turn_id=turn_id)
                        except Exception as exc:
                            observation = {
                                "ok": False,
                                "type": "TOOL_ERROR",
                                "capability": call.name,
                                "reason": str(exc),
                            }
                            self._emit(EventType.TOOL_FAILED, observation, turn_id=turn_id)

                turn_items.append({
                    "role": "tool",
                    "name": call.name,
                    "content": observation,
                })
                self.state.record_event("tool_observation", observation)

        result = f"Stopped after max_steps={self.max_steps} without a final answer."
        self._commit_turn(objective, turn_items, result)
        self.state.record_event("max_steps", {"reason": result})
        self._emit(EventType.TURN_FAILED, {"reason": result}, turn_id=turn_id)
        return result
