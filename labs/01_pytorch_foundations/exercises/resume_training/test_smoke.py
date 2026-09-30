"""Infrastructure checks; none implements learner state capture or restore."""

from importlib import import_module
from pathlib import Path

import pytest

torch = pytest.importorskip("torch", reason="Install the optional training group")
fixture = import_module("labs.01_pytorch_foundations.exercises.resume_training.fixture")


def test_separate_tiny_checkpoint_io(tmp_path: Path) -> None:
    # A scalar calibration artifact, not a training-resume state.
    path = tmp_path / "scalar.pt"
    fixture.save_checkpoint(path, {"gain": torch.tensor([2.0]), "version": 1})
    saved = fixture.load_checkpoint(path)
    assert saved["version"] == 1
    torch.testing.assert_close(saved["gain"] * 3, torch.tensor([6.0]))


def test_corrupt_checkpoint_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.pt"
    path.write_bytes(b"not a checkpoint")
    with pytest.raises(ValueError, match="checkpoint"):
        fixture.load_checkpoint(path)


def test_checkpoint_rejects_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "list.pt"
    torch.save([1, 2], path)
    with pytest.raises(ValueError, match="mapping"):
        fixture.load_checkpoint(path)


def test_fixture_consumes_short_batch_and_advances_epoch() -> None:
    model, optimizer, cursor = fixture.new_run()
    cursor, trace = fixture.advance(model, optimizer, cursor, 7)
    assert [len(row["ids"]) for row in trace] == [3, 3, 3, 1, 3, 3, 3]
    assert [row["global_step"] for row in trace] == list(range(1, 8))
    assert [row["epoch"] for row in trace] == [0, 0, 0, 0, 1, 1, 1]
    assert sorted(x for row in trace[:4] for x in row["ids"]) == list(fixture.TRAIN_IDS)
    assert (cursor.epoch, cursor.global_step, cursor.next_batch_offset) == (1, 7, 9)


def test_fresh_process_fixture_runs_without_learner_solution(tmp_path: Path) -> None:
    result = fixture.fresh_run(tmp_path / "continuous.pt")
    assert len(result["trace"]) == 7
    assert result["cursor"]["global_step"] == 7
    assert result["pid"] != __import__("os").getpid()


def test_loader_rejects_arbitrary_class(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.pt"
    torch.save(Path("untrusted"), path)
    with pytest.raises(ValueError, match="checkpoint"):
        fixture.load_checkpoint(path)


def test_loader_bookkeeping_does_not_consume_dropout_rng() -> None:
    x, y = torch.ones(2, 4), torch.tensor([0, 1])
    before = torch.get_rng_state().clone()
    batch_x, batch_y = next(iter(fixture.batch_loader(x, y)))
    assert torch.equal(torch.get_rng_state(), before)
    assert torch.equal(batch_x, x)
    assert torch.equal(batch_y, y)
