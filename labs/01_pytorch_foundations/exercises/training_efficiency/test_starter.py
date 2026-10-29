"""Mandatory CPU learner contracts: uneven rows, stale gradients, one update."""

from copy import deepcopy
from importlib import import_module

import pytest

from roadmap_tools.exercise import exercise_call

torch = pytest.importorskip("torch", reason="Install --group training")
starter = import_module("labs.01_pytorch_foundations.exercises.training_efficiency.starter")


@pytest.mark.parametrize("sizes", [(2, 2), (3, 1, 2), (1, 4)])
def test_matches_full_batch_including_optimizer_state(sizes: tuple[int, ...]) -> None:
    torch.manual_seed(19)
    model = torch.nn.Linear(3, 2, dtype=torch.float64)
    full = deepcopy(model)
    opt = torch.optim.SGD(model.parameters(), lr=0.03, momentum=0.7)
    ref = torch.optim.SGD(full.parameters(), lr=0.03, momentum=0.7)
    calls = []
    opt.register_step_post_hook(lambda *_: calls.append("step"))
    x = torch.arange(sum(sizes) * 3, dtype=torch.float64).reshape(-1, 3) / 9
    y = torch.sin(x[:, :2])
    loss_fn = torch.nn.MSELoss()
    for _ in range(2):
        for p in model.parameters():
            p.grad = torch.full_like(p, 99)  # must be cleared, including on second update
        ref.zero_grad(set_to_none=True)
        expected = loss_fn(full(x), y)
        expected.backward()
        ref.step()
        batches = list(zip(x.split(sizes), y.split(sizes), strict=True))
        observed = exercise_call(starter.accumulated_step, model, opt, batches, loss_fn)
        assert observed == pytest.approx(expected.item(), abs=1e-12)
        for actual, wanted in zip(model.parameters(), full.parameters(), strict=True):
            torch.testing.assert_close(actual, wanted, atol=1e-12, rtol=1e-12)
            torch.testing.assert_close(actual.grad, wanted.grad, atol=1e-12, rtol=1e-12)
            torch.testing.assert_close(
                opt.state[actual]["momentum_buffer"], ref.state[wanted]["momentum_buffer"]
            )
    assert len(calls) == 2


@pytest.mark.parametrize("empty_row", [False, True])
def test_empty_batch_rejected_without_update(empty_row: bool) -> None:
    model = torch.nn.Linear(2, 1)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    before = deepcopy(model.state_dict())
    batches = [(torch.empty(0, 2), torch.empty(0, 1))] if empty_row else []
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.accumulated_step, model, opt, batches, torch.nn.MSELoss())
    for name, tensor in model.state_dict().items():
        assert torch.equal(tensor, before[name])
