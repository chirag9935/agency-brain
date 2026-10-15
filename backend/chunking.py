def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
        """Split text into overlapping chunks by character count."""
        chunks = []
        start = 0
        while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                start += chunk_size - overlap
        return [c.strip() for c in chunks if c.strip()]        