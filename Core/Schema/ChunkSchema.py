from dataclasses import dataclass, asdict, field
from typing import Any

@dataclass
class TextChunk:
    """A stored text unit.

    ``metadata`` is deliberately a JSON-like dictionary rather than a fixed
    collection of OCR fields.  Existing benchmark chunks still use the first
    six fields; specialised corpora can retain stable source identifiers and
    provenance without changing the generic retrieval API.
    """
    tokens: int
    chunk_id: str
    content: str
    doc_id: str
    index: int
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def as_dict(self):
        return asdict(self)

    def __setstate__(self, state):
        """Read chunk pickles created before provenance metadata existed."""
        self.__dict__.update(state)
        if not hasattr(self, "metadata") or self.metadata is None:
            self.metadata = {}
