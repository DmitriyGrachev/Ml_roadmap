"""Independent CPU example using PyTorch's attention operator."""

from __future__ import annotations

import json


def run_example() -> dict[str, object]:
    """Demonstrate a combined causal and padding mask on synthetic vectors."""
    import torch
    from torch.nn import functional as functional

    generator = torch.Generator().manual_seed(23)
    q = torch.randn((1, 2, 3, 4), generator=generator, dtype=torch.float64)
    k = torch.randn((1, 2, 4, 4), generator=generator, dtype=torch.float64)
    v = torch.randn((1, 2, 4, 4), generator=generator, dtype=torch.float64)
    causal = torch.ones((3, 4), dtype=torch.bool).tril()
    valid_key = torch.tensor([True, True, True, False])
    allowed = (causal & valid_key).view(1, 1, 3, 4)
    output = functional.scaled_dot_product_attention(q, k, v, attn_mask=allowed, dropout_p=0.0)

    future_changed = v.clone()
    future_changed[..., 2, :] = 1_000.0
    future_output = functional.scaled_dot_product_attention(
        q, k, future_changed, attn_mask=allowed, dropout_p=0.0
    )
    padded_changed = v.clone()
    padded_changed[..., 3, :] = -1_000.0
    padded_output = functional.scaled_dot_product_attention(
        q, k, padded_changed, attn_mask=allowed, dropout_p=0.0
    )
    return {
        "evidence": "LIBRARY_SDPA_SYNTHETIC_ONLY",
        "output_shape": list(output.shape),
        "finite_output": bool(torch.isfinite(output).all()),
        "future_change_first_query_max_abs": float(
            (output[..., :1, :] - future_output[..., :1, :]).abs().max()
        ),
        "padded_change_max_abs": float((output - padded_output).abs().max()),
    }


if __name__ == "__main__":
    print(json.dumps(run_example(), sort_keys=True))
