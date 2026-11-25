"""Turn the markdown guide in data/ into retrievable chunks."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_chunks(data_dir: Path = DATA_DIR) -> list[str]:
    """One chunk per '##' section, each prefixed with its document title.

    Keeping the title on every chunk means a retrieved passage still says which
    guide it came from ("Accessibility ..." vs "Visiting ...").
    """
    chunks: list[str] = []
    for path in sorted(data_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        title = title.removeprefix("# ").strip()
        for section in sections:
            heading, _, body = section.partition("\n")
            chunks.append(f"{title} / {heading.strip()}\n{' '.join(body.split())}")
    return chunks
