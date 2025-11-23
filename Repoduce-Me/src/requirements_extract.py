import re
import os
from pathlib import Path
from typing import Set, Optional, List

class RequirementsExtractor:
    """
    Scans a cloned repository directory to identify external Python package dependencies
    by looking for 'import' and 'from ... import' statements.
    It compiles a list of unique, external dependencies into a requirements.txt file.
    """

    STANDARD_LIBRARY: Set[str] = {
        'os', 'sys', 'pathlib', 're', 'json', 'csv', 'math', 'time', 'datetime', 
        'typing', 'collections', 'itertools', 'functools', 'logging', 'argparse',
        'subprocess', 'shutil', 'tempfile', 'threading', 'queue', 'socket',
        'http', 'urllib', 'xml', 'html', 'unittest', 'doctest', 'warnings', 
        'dataclasses', 'abc', 'enum', 'decimal', 'io', 'pickle', 'gzip', 'zipfile',
        'hashlib', 'base64', 'asyncio'
    }

    IMPORT_TO_INSTALL_NAME: dict[str, str] = {
        'PIL': 'Pillow',
        # Add other common mis-matches here if encountered:
        # 'cv2': 'opencv-python', 
        # 'yaml': 'PyYAML',
    }

    def __init__(self, output_dir: str = "tmp"):
        """
        Initializes the extractor with the directory where the requirements.txt 
        will be written.
        """
        self.output_dir = Path(output_dir)
        self.output_file = self.output_dir / "requirements.txt"
        self.all_dependencies: Set[str] = set()

    def _extract_module_name(self, line: str) -> Optional[str]:
        """
        Extracts the top-level module name from an import statement line.
        """
        line = line.strip()

        # Regex for 'import <module> [as alias]'
        match_import = re.match(r"import\s+([a-zA-Z0-9_]+)", line)
        if match_import:
            module = match_import.group(1)
            return module

        # Regex for 'from <module>.<sub_module> | from <module> import ...'
        match_from = re.match(r"from\s+([a-zA-Z0-9_\.]+)\s+import", line)
        if match_from:
            module_full = match_from.group(1)
            module = module_full.split('.')[0]
            
            # Filter out relative imports immediately
            if module.startswith('.'):
                return None
            
            return module
            
        return None

    def analyze_repo(self, repo_path: Path):
        """
        Walks the repository directory, analyzes Python files, and writes dependencies.
        """
        repo_path = Path(repo_path)
        print(f"[INFO] Starting dependency analysis in: {repo_path}")
        
        if not repo_path.is_dir():
            print(f"[ERROR] Repository path not found: {repo_path}")
            return

        for root, _, files in os.walk(repo_path):
            if any(part.startswith('.') for part in Path(root).parts):
                continue
                
            for file_name in files:
                if file_name.endswith(".py"):
                    file_path = Path(root) / file_name
                    self._analyze_file(file_path)

        # 1. Filter out standard library modules
        external_dependencies = self.all_dependencies - self.STANDARD_LIBRARY
        
        # 2. Apply the name mapping (e.g., PIL -> Pillow)
        final_dependencies = set()
        for dep in external_dependencies:
            install_name = self.IMPORT_TO_INSTALL_NAME.get(dep, dep)
            final_dependencies.add(install_name)
            
        sorted_dependencies = sorted(list(final_dependencies))
        
        self._write_requirements_file(sorted_dependencies)

    def _analyze_file(self, file_path: Path):
        """Reads a single Python file and extracts dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    module_name = self._extract_module_name(line)
                    if module_name:
                        self.all_dependencies.add(module_name)
                        
        except Exception as e:
            print(f"[WARNING] Could not read or analyze file {file_path}: {e}")

    def _write_requirements_file(self, dependencies: List[str]):
        """Writes the collected external dependencies to requirements.txt."""
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.output_file, 'w') as f:
                for dep in dependencies:
                    f.write(f"{dep}\n")
            
            print(f"\n[SUCCESS] Extracted {len(dependencies)} external dependencies.")
            print(f"[SUCCESS] Requirements file written to: {self.output_file.resolve()}")
            
        except Exception as e:
            print(f"[ERROR] Failed to write requirements.txt: {e}")

if __name__ == "__main__":
    # Example usage for testing
    TEST_DIR = Path("test_repo_for_reqs")
    TEST_DIR.mkdir(exist_ok=True)
    
    (TEST_DIR / "test1.py").write_text("""
import os
import requests 
import PIL.Image as Image # <-- This should be mapped to Pillow
from numpy import array 
import pandas as pd 
from . import local_file 
from typing import Optional 
import sys
""")
    
    (TEST_DIR / "sub_dir").mkdir(exist_ok=True)
    (TEST_DIR / "sub_dir" / "test2.py").write_text("""
from sklearn.metrics import accuracy_score 
import matplotlib.pyplot as plt 
import re 
""")

    extractor = RequirementsExtractor(output_dir="tmp_output")
    extractor.analyze_repo(TEST_DIR)

    import shutil
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    shutil.rmtree("tmp_output", ignore_errors=True)