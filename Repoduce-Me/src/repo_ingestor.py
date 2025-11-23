from pathlib import Path
from typing import Iterable, Optional

from constructor_model import ConstructorModel 


class RepoIngestor:
    """
    Read a repository folder and send its files to an LLM.

    - Walks the directory tree.
    - Filters by extension and size.
    - Skips typical junk/binary directories.
    - Sends each file (path + content) to the LLM.
    """

    def __init__(
        self,
        root_dir: str,
        model: Optional[ConstructorModel] = None,
        include_exts: Optional[set[str]] = None,
        exclude_dirs: Optional[set[str]] = None,
        max_file_size_kb: int = 64,
    ) -> None:
        self.root_dir = Path(root_dir).resolve()
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Repo folder not found: {self.root_dir}")

        self.model = model or ConstructorModel(model="gpt-4.1-mini")
        self.include_exts = include_exts or {".py", ".md", ".txt", ".json", ".yml", ".yaml"}
        self.exclude_dirs = exclude_dirs or {".git", "__pycache__", "node_modules", ".venv", "venv"}

        self.max_file_size_kb = max_file_size_kb


    def iter_files(self) -> Iterable[Path]:
        """
        Yield paths of candidate files under root_dir.
        """
        for path in self.root_dir.rglob("*"):
            if not path.is_file():
                continue

            if any(part in self.exclude_dirs for part in path.parts):
                continue

            if path.suffix and path.suffix.lower() not in self.include_exts:
                continue

            size_kb = path.stat().st_size / 1024
            if size_kb > self.max_file_size_kb:
                continue

            yield path

    def read_file(self, path: Path) -> str:
        """
        Read a file safely as text.
        """
        # basic binary guard
        try:
            data = path.read_bytes()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {path}: {e}") from e

        if b"\x00" in data:
            raise ValueError(f"File looks binary, skipping: {path}")

        return data.decode("utf-8", errors="ignore")


    def ingest(self) -> None:
        """
        Iterate over all filtered files and send them to the LLM one by one.
        """
        for file_path in self.iter_files():
            try:
                content = self.read_file(file_path)
            except Exception as e:
                print(f"Skipping {file_path}: {type(e).__name__} - {e}")
                continue

            rel_path = file_path.relative_to(self.root_dir)

            prompt = (
                "You are building an internal memory of a code repository.\n"
                "I will send you one file at a time. For each file, you should:\n"
                "- Note the file path\n"
                "- Note the main purpose of the file\n"
                "- Note any important classes, functions, or configuration.\n\n"
                f"File path: {rel_path}\n"
                "File content:\n"
                "```python\n"
                f"{content}\n"
                "```"
                "Your task is to remember this and to be able to generate code base on this repository. "
            )

            self.model.invoke(prompt)
        print(self.model.invoke("tell me what you know about this repository"))
        print(f"Processed {rel_path}")
    
    def explain_repo(self) -> str:
        return self.model.invoke("Explain now what you did ") 

if __name__ == "__main__":
    repo_path = "tmp" 

    ingestor = RepoIngestor(root_dir=repo_path)
    ingestor.ingest()
    # print(ingestor.explain_repo())