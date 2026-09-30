"""Offline CPU smoke on synthetic shape images; not a quality benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, Subset


class ShapeImages(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Tiny local vertical/horizontal bar images with fixed noise."""

    def __init__(self) -> None:
        generator = torch.Generator().manual_seed(41)
        images: list[torch.Tensor] = []
        labels: list[int] = []
        for index in range(26):
            image = torch.rand((1, 4, 4), generator=generator) * 0.05
            if index % 2 == 0:
                image[0, :, 1] += 0.9
            else:
                image[0, 2, :] += 0.9
            images.append(image)
            labels.append(index % 2)
        self.images = images
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.images[index], torch.tensor(self.labels[index], dtype=torch.long)


class ShapeNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(nn.Flatten(), nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 2))

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        logits: torch.Tensor = self.layers(images)
        return logits


def run_smoke(output_dir: Path) -> dict[str, object]:
    """Exercise all lifecycle stages locally and return mechanical run facts."""
    torch.manual_seed(13)
    device = torch.device("cpu")
    dataset = ShapeImages()
    train_loader = DataLoader(
        Subset(dataset, list(range(19))),
        batch_size=6,
        shuffle=True,
        generator=torch.Generator().manual_seed(13),
    )
    validation_loader = DataLoader(Subset(dataset, list(range(19, 26))), batch_size=3)
    model = ShapeNet().to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.15)
    criterion = nn.CrossEntropyLoss()
    for _ in range(2):
        model.train()
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            for images, labels in validation_loader:
                _ = criterion(model(images.to(device)), labels.to(device))

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "shape-smoke.pt"
    torch.save({"model_state": model.state_dict(), "epoch": 2}, checkpoint)
    loaded = torch.load(checkpoint, map_location=device, weights_only=True)
    restored = ShapeNet().to(device)
    restored.load_state_dict(loaded["model_state"])
    restored.eval()
    predictions: list[int] = []
    with torch.no_grad():
        for images, _ in validation_loader:
            predictions.extend(restored(images.to(device)).argmax(dim=1).tolist())
    return {
        "task": "synthetic object-shape smoke",
        "train_count": 19,
        "validation_count": 7,
        "epochs": 2,
        "checkpoint_reloaded": all(
            torch.equal(a, b)
            for a, b in zip(model.parameters(), restored.parameters(), strict=True)
        ),
        "prediction_count": len(predictions),
        "quality_claim": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local PyTorch lifecycle smoke")
    parser.add_argument("--output", type=Path, default=Path("generated-reports/pytorch/smoke"))
    arguments = parser.parse_args()
    print(json.dumps(run_smoke(arguments.output), sort_keys=True))


if __name__ == "__main__":
    main()
