"""Learner-owned scaled dot-product attention boundary."""

from torch import Tensor


def attention(q: Tensor, k: Tensor, v: Tensor, allowed: Tensor) -> Tensor:
    """Return masked scaled dot-product attention without dropout.

    CPU float32/float64 tensors have shapes q [B,H,Tq,Dh], k [B,H,Tk,Dh],
    v [B,H,Tk,Dh]. A bool mask [B,1,Tq,Tk] broadcasts over heads and True
    permits a key. Reject malformed, nonfinite, and all-masked query rows
    with ValueError. Keep the gradient path through q, k, and v.
    """
    raise NotImplementedError("Implement masked scaled dot-product attention")
