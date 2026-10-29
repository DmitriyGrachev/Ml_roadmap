"""Fixed neutral author data and local random model; never learner project data."""

from typing import Any

CORPUS = [
    {
        "id": "author-a",
        "family": "amber",
        "split": "train",
        "messages": [
            {"role": "user", "content": "repeat amber"},
            {"role": "assistant", "content": "amber"},
        ],
    },
    {
        "id": "author-b",
        "family": "birch",
        "split": "train",
        "messages": [
            {"role": "user", "content": "repeat birch"},
            {"role": "assistant", "content": "birch"},
        ],
    },
    {
        "id": "author-c",
        "family": "coral",
        "split": "validation",
        "messages": [
            {"role": "user", "content": "repeat coral"},
            {"role": "assistant", "content": "coral"},
        ],
    },
    {
        "id": "author-d",
        "family": "dune",
        "split": "holdout",
        "messages": [
            {"role": "user", "content": "repeat dune"},
            {"role": "assistant", "content": "dune"},
        ],
    },
]


def tiny_components() -> tuple[Any, Any]:
    """Construct only in memory, without pretrained loaders or Hub access."""
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import WhitespaceSplit
    from transformers import LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast

    words = [
        "<pad>",
        "<unk>",
        "<eos>",
        "user",
        "assistant",
        "repeat",
        "amber",
        "birch",
        "coral",
        "dune",
    ]
    backend = Tokenizer(
        WordLevel(dict(zip(words, range(len(words)), strict=True)), unk_token="<unk>")
    )
    backend.pre_tokenizer = WhitespaceSplit()
    tokenizer_type: Any = PreTrainedTokenizerFast  # lazy upstream constructor is untyped
    tokenizer = tokenizer_type(
        tokenizer_object=backend, pad_token="<pad>", unk_token="<unk>", eos_token="<eos>"
    )
    tokenizer.chat_template = (
        "{% for message in messages %}{{ message['role'] + ' ' }}"
        "{% if message['role'] == 'assistant' %}{% generation %}"
        "{{ message['content'] + ' <eos> ' }}{% endgeneration %}"
        "{% else %}{{ message['content'] + ' ' }}{% endif %}{% endfor %}"
        "{% if add_generation_prompt %}{{ 'assistant ' }}{% endif %}"
    )
    config = LlamaConfig(
        vocab_size=len(words),
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=1,
        max_position_embeddings=32,
        pad_token_id=0,
        eos_token_id=2,
        attention_dropout=0.0,
        use_cache=False,
    )
    config._attn_implementation = "eager"
    model_type: Any = LlamaForCausalLM  # decorated upstream constructor is untyped
    return model_type(config), tokenizer


def author_training_rows(tokenizer: Any) -> list[dict[str, list[int]]]:
    """Only the two fixed training rows; no reusable learner validation/splitting."""
    encoded = []
    for row in CORPUS[:2]:
        item = tokenizer.apply_chat_template(
            row["messages"], tokenize=True, return_dict=True, return_assistant_tokens_mask=True
        )
        ids = item["input_ids"]
        mask = item["assistant_masks"]
        assert mask == [0, 0, 0, 0, 1, 1]
        encoded.append(
            {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": [-100] * 4 + ids[4:]}
        )
    return encoded
