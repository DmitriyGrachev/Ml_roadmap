"""CPU preflight negative case; never runs GPU work."""

from importlib import import_module
from types import SimpleNamespace

import pytest


def test_cpu_cannot_claim_cuda_success() -> None:
    module = import_module("labs.01_pytorch_foundations.exercises.training_efficiency.gpu_runner")
    with pytest.raises(RuntimeError, match="NOT_RUN"):
        module.require_cuda(SimpleNamespace(is_available=lambda: False))
