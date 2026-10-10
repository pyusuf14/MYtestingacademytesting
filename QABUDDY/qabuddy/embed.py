"""Embedding via BGE (FastEmbed/ONNX) — lazy singleton to avoid reload."""
from __future__ import annotations

from typing import Any


class Embedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model: Any = None

    def _load(self):
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = list(model.embed(list(texts)))
        return [v.tolist() for v in vectors]

    def dim(self) -> int:
        if not self.embed([""]):
            return 0
        return len(self.embed([""])[0])


_embedder: Embedder | None = None


def get_embedder(model_name: str) -> Embedder:
    global _embedder
    if _embedder is None or _embedder.model_name != model_name:
        _embedder = Embedder(model_name)
    return _embedder
