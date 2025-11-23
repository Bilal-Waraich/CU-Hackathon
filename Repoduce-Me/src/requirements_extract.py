import re
import os
from pathlib import Path
from typing import Set, Optional, List, Dict
import shutil
import sys

# Configuration constants (must match main.py)
TMP_DIR = "tmp"
VENV_DIR_NAME = ".venv_repro" # Use name only for robust exclusion


class RequirementsExtractor:
    """
    Scans a cloned repository directory to identify external Python package dependencies
    by looking for 'import' and 'from ... import' statements.
    """

    # --- 1. Comprehensive Standard Library Modules (Exclusion List) ---
    STANDARD_LIBRARY: Set[str] = {
        '__future__', '__main__', 'abc', 'argparse', 'array', 'asyncio',
        'base64', 'builtins', 'csv', 'collections', 'copy', 'ctypes', 
        'datetime', 'decimal', 'json', 'math', 'os', 'pathlib', 're', 
        'shutil', 'sys', 'subprocess', 'time', 'typing', 'warnings',
        'threading', 'tempfile', 'unittest', 'xml', 'zipfile',
        'itertools', 'functools', 'logging', 'io', 'random', 'hashlib',
        'queue', 'socket', 'http', 'ssl', 'uuid', 'operator', 'pickle',
        'xml', 'configparser'
    }

    # --- 2. Module to Package Mapping (e.g., 'PIL' -> 'Pillow') ---
    MODULE_TO_PACKAGE: Dict[str, str] = {
        'yaml': 'pyyaml',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'skimage': 'scikit-image',
        'scipy': 'scipy',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy',
        'torch': 'torch',
        'tensorflow': 'tensorflow',
        'pandas': 'pandas',
        'flask': 'flask',
        'django': 'django',
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'lxml': 'lxml',
        'tqdm': 'tqdm',
        'seaborn': 'seaborn',
        'sklearn': 'scikit-learn',
        'six': 'six',
        'cffi': 'cffi',
    }

    # --- 3. CRITICAL DEBUG BLACKLIST ---
    # Packages that cause persistent build errors or are incorrectly detected.
    DEBUG_BLACKLIST: Set[str] = {
        'enum', 
        'enum34', 
        'pkg_resources', 
        'setuptools',
        'distutils',
        'astropilot',
        'concurrent',
        'contextlib'
    }

    def __init__(self, output_dir: str = "tmp"):
        self.output_dir = Path(output_dir)
        self.output_file = self.output_dir / "requirements.txt"
        self.all_dependencies: Set[str] = set()

    def _extract_module_name(self, line: str) -> Optional[str]:
        """Tries to extract the top-level module name from an import statement."""

        # Regex for 'import <module>' or 'import <module> as <alias>'
        match_import = re.match(r'^\s*import\s+([a-zA-Z0-9_]+)', line)
        if match_import:
            return match_import.group(1)

        # Regex for 'from <module> import ...'
        match_from = re.match(r'^\s*from\s+([a-zA-Z0-9_]+)', line)
        if match_from:
            return match_from.group(1)

        return None

    def _analyze_file(self, file_path: Path):
        """Reads a file and extracts dependencies."""
        if file_path.name.lower() in ['setup.py', 'requirements.txt', 'test.py', 'conftest.py']:
            return

        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding='latin-1')
            except Exception as e:
                print(f"[WARNING] Skipping file due to encoding/read error: {file_path} ({e})")
                return
        except Exception as e:
            print(f"[WARNING] Skipping file due to read error: {file_path} ({e})")
            return

        try:
            for line in content.splitlines():
                module_name = self._extract_module_name(line)
                if module_name:
                    self.all_dependencies.add(module_name)

        except Exception as e:
            print(f"[WARNING] Could not analyze imports in file {file_path}: {e}. Skipping file.")

    def _is_external(self, module_name: str) -> bool:
        """Checks if a module is external (not standard library or blacklisted)."""
        if module_name in self.STANDARD_LIBRARY:
            return False
        if module_name in self.DEBUG_BLACKLIST:
            return False

        # Map common internal names (e.g., 'PIL') to package names (e.g., 'Pillow')
        return True

    def _map_to_package_names(self, dependencies: Set[str]) -> List[str]:
        """Maps module names to official package names and filters."""
        package_names: Set[str] = set()

        for dep in dependencies:
            if not self._is_external(dep):
                continue

            # Map common internal names (e.g., 'PIL') to package names (e.g., 'Pillow')
            package = self.MODULE_TO_PACKAGE.get(dep, dep)
            package_names.add(package)

        # Sort and return as list
        return sorted(list(package_names))

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
            print(f"[ERROR] Failed to write requirements file: {e}", file=sys.stderr)
            raise

    def analyze_repo(self, repo_path: Path):
        """Main method to traverse the repository and extract dependencies."""
        print(f"[INFO] Starting dependency analysis in: {repo_path}")

        # 1. Clear previous state
        self.all_dependencies = set()

        # 2. Traverse repository
        for root, dirs, files in os.walk(repo_path):
            current_path = Path(root)

            # Exclusion Logic: Skip temporary and virtual environment directories
            # We exclude the venv by name, as it could appear in /tmp or /workspace
            if VENV_DIR_NAME in dirs:
                dirs.remove(VENV_DIR_NAME)
            if TMP_DIR in dirs and Path(root).name != TMP_DIR: # Don't accidentally skip the repo if it's named 'tmp'
                dirs.remove(TMP_DIR)
            
            # The workspace directory is the parent of the repository when --tmp is not used, 
            # so we only traverse *into* the cloned repo (which os.walk handles starting from repo_path)

            for file_name in files:
                if file_name.endswith('.py'):
                    file_path = current_path / file_name
                    self._analyze_file(file_path)

        # 3. Map to package names and finalize the list (this handles the filtering)
        final_dependencies = self._map_to_package_names(self.all_dependencies)

        # 4. Write the final requirements file
        self._write_requirements_file(final_dependencies)