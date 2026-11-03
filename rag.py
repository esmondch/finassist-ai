
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


DATA_DIR = Path(__file__).parent / "data"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_WORDS = 120
CHUNK_OVERLAP = 25


@dataclass
class DocumentChunk:
    text: str
    source: str
    chunk_id: int


class BankingRAG:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.chunks = self._load_chunks()

        if not self.chunks:
            raise ValueError("No banking policy documents were found.")

        texts = [chunk.text for chunk in self.chunks]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")

        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def _load_chunks(self):
        chunks = []

        for path in sorted(DATA_DIR.glob("*.md")):
            content = path.read_text(encoding="utf-8")

            # Split at section headings to preserve topic boundaries.
            sections = []
            current_heading = path.stem.replace("_", " ").title()
            current_lines = []

            for line in content.splitlines():
                if line.startswith("#"):
                    if current_lines:
                        sections.append(
                            (current_heading, "\n".join(current_lines))
                        )

                    current_heading = line.lstrip("#").strip()
                    current_lines = []
                else:
                    current_lines.append(line)

            if current_lines:
                sections.append(
                    (current_heading, "\n".join(current_lines))
                )

            for heading, section_text in sections:
                words = section_text.split()

                if not words:
                    continue

                start = 0

                while start < len(words):
                    end = min(start + CHUNK_WORDS, len(words))
                    passage = " ".join(words[start:end]).strip()

                    if passage:
                        chunks.append(
                            DocumentChunk(
                                text=f"Topic: {heading}\n{passage}",
                                source=path.name,
                                chunk_id=len(chunks),
                            )
                        )

                    if end == len(words):
                        break

                    start = end - CHUNK_OVERLAP

        return chunks

    def retrieve(self, question, k=3):
        query_embedding = self.model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")

        k = min(k, len(self.chunks))
        scores, indices = self.index.search(query_embedding, k)

        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            chunk = self.chunks[int(idx)]

            results.append({
                "text": chunk.text,
                "source": chunk.source,
                "chunk_id": chunk.chunk_id,
                "score": float(score),
            })

        return results



if __name__ == "__main__":
    rag = BankingRAG()

    test_questions = [
        "What should I do if I gave my banking OTP to a scammer?",
        "How do I block my lost DBS credit card?",
        "How do I dispute an unauthorised credit card transaction?",
        "Can DBS cancel a pending card transaction?",
        "What fees apply when I use my DBS debit card overseas?"
    ]

    print(f"\nTotal document chunks: {len(rag.chunks)}")
    print("=" * 80)

    for question in test_questions:
        print(f"\nQUESTION: {question}")
        print("-" * 80)

        results = rag.retrieve(question, k=3)

        for i, result in enumerate(results, start=1):
            print(f"\nRank: {i}")
            print(f"Source: {result['source']}")
            print(f"Chunk: {result['chunk_id']}")
            print(f"Similarity: {result['score']:.3f}")
            print(result["text"])

