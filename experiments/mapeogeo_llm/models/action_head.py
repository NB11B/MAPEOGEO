"""Compact structured action and public-state pointer prediction head."""

from torch import Tensor, nn


class ActionHead(nn.Module):
    def __init__(self, d_model: int, num_actions: int, num_pointer_slots: int = 0) -> None:
        super().__init__()
        if d_model <= 0 or num_actions <= 0 or num_pointer_slots < 0:
            raise ValueError("invalid action-head dimensions")
        self.action_projection = nn.Linear(d_model, num_actions)
        self.pointer_projection = nn.Linear(d_model, num_pointer_slots) if num_pointer_slots else None

    def forward(self, hidden_states: Tensor) -> dict[str, Tensor]:
        if hidden_states.ndim != 3:
            raise ValueError("hidden_states must have shape [batch, sequence, model]")
        output = {"action_logits": self.action_projection(hidden_states)}
        if self.pointer_projection is not None:
            output["pointer_logits"] = self.pointer_projection(hidden_states)
        return output
