"""Learner contract against PyTorch's CPU attention reference."""

from importlib import import_module

import pytest

from roadmap_tools.exercise import exercise_call

torch = pytest.importorskip("torch", reason="Install the optional training group")
functional = torch.nn.functional
starter = import_module("labs.02_huggingface_models.attention_mechanics.starter")


@pytest.mark.parametrize(
    ("dtype", "rtol", "atol"),
    [(torch.float32, 1e-5, 1e-6), (torch.float64, 1e-7, 1e-9)],
)
def test_matches_sdpa_and_gradients(dtype: object, rtol: float, atol: float) -> None:
    generator = torch.Generator().manual_seed(79)
    q = torch.randn((2, 3, 4, 5), generator=generator, dtype=dtype, requires_grad=True)
    k = torch.randn((2, 3, 6, 5), generator=generator, dtype=dtype, requires_grad=True)
    v = torch.randn((2, 3, 6, 5), generator=generator, dtype=dtype, requires_grad=True)
    allowed = torch.randint(0, 2, (2, 1, 4, 6), generator=generator, dtype=torch.bool)
    allowed[..., 0] = True

    actual = exercise_call(starter.attention, q, k, v, allowed)
    expected = functional.scaled_dot_product_attention(q, k, v, attn_mask=allowed, dropout_p=0.0)
    assert actual.shape == (2, 3, 4, 5)
    torch.testing.assert_close(actual, expected, rtol=rtol, atol=atol)
    actual.square().sum().backward(retain_graph=True)
    actual_grads = [tensor.grad.clone() for tensor in (q, k, v)]
    for tensor in (q, k, v):
        tensor.grad = None
    expected.square().sum().backward()
    for actual_grad, tensor in zip(actual_grads, (q, k, v), strict=True):
        assert tensor.grad is not None
        assert torch.isfinite(actual_grad).all()
        torch.testing.assert_close(actual_grad, tensor.grad, rtol=rtol, atol=atol)


def test_padding_values_have_no_influence() -> None:
    q = torch.tensor([[[[1.0, 0.0], [0.0, 1.0]]]])
    k = torch.tensor([[[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]]])
    v = torch.tensor([[[[2.0, 20.0], [4.0, 40.0], [900.0, 9000.0]]]])
    allowed = torch.tensor([[[[True, True, False], [True, True, False]]]])
    original = exercise_call(starter.attention, q, k, v, allowed)
    changed_v = v.clone()
    changed_v[..., 2, :] = -900.0
    changed = exercise_call(starter.attention, q, k, changed_v, allowed)
    torch.testing.assert_close(original, changed)
    assert original[..., 0].max().item() <= 4.0
    assert original[..., 1].max().item() <= 40.0


def test_causal_mask_blocks_future_value() -> None:
    q = torch.zeros((1, 1, 3, 2))
    k = torch.zeros((1, 1, 3, 2))
    v = torch.tensor([[[[1.0, 10.0], [3.0, 30.0], [50.0, 500.0]]]])
    allowed = torch.ones((1, 1, 3, 3), dtype=torch.bool).tril()
    actual = exercise_call(starter.attention, q, k, v, allowed)
    torch.testing.assert_close(actual[0, 0, :, 0], torch.tensor([1.0, 2.0, 18.0]))
    changed_v = v.clone()
    changed_v[..., 2, :] = -50.0
    changed = exercise_call(starter.attention, q, k, changed_v, allowed)
    torch.testing.assert_close(actual[..., :2, :], changed[..., :2, :])


@pytest.mark.parametrize(
    "bad",
    [
        "all_masked",
        "wrong_mask_shape",
        "wrong_mask_dtype",
        "wrong_value_width",
        "zero_width",
        "nonfinite",
        "key_value_length",
        "query_key_width",
        "query_key_heads",
        "value_heads",
        "batch_mismatch",
        "query_rank",
        "key_rank",
        "value_rank",
        "mask_rank",
        "integer_dtype",
        "bool_dtype",
        "mixed_dtype",
    ],
)
def test_invalid_inputs_raise_value_error(bad: str) -> None:
    q = torch.ones((1, 2, 2, 3))
    k = torch.ones((1, 2, 3, 3))
    v = torch.ones((1, 2, 3, 3))
    allowed = torch.ones((1, 1, 2, 3), dtype=torch.bool)
    if bad == "all_masked":
        allowed[0, 0, 1] = False
    elif bad == "wrong_mask_shape":
        allowed = allowed.expand(1, 2, 2, 3)
    elif bad == "wrong_mask_dtype":
        allowed = allowed.float()
    elif bad == "wrong_value_width":
        v = v[..., :2]
    elif bad == "zero_width":
        q = q[..., :0]
        k = k[..., :0]
    elif bad == "key_value_length":
        v = v[..., :2, :]
    elif bad == "query_key_width":
        k = k[..., :2]
    elif bad == "query_key_heads":
        k = k[:, :1]
    elif bad == "value_heads":
        v = v[:, :1]
    elif bad == "batch_mismatch":
        k = k.expand(2, 2, 3, 3)
    elif bad == "query_rank":
        q = q[0]
    elif bad == "key_rank":
        k = k[0]
    elif bad == "value_rank":
        v = v[0]
    elif bad == "mask_rank":
        allowed = allowed[0]
    elif bad == "integer_dtype":
        q, k, v = q.long(), k.long(), v.long()
    elif bad == "bool_dtype":
        q, k, v = q.bool(), k.bool(), v.bool()
    elif bad == "mixed_dtype":
        k = k.double()
    else:
        q[0, 0, 0, 0] = float("nan")
    with pytest.raises(ValueError):  # noqa: PT011 - diagnostic text belongs to learner
        exercise_call(starter.attention, q, k, v, allowed)
