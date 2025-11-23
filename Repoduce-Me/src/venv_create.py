import sys
import subprocess
from pathlib import Path
from typing import List
import shutil 
import re

# Configuration constants (must match main.py)
TMP_DIR = "tmp"
VENV_DIR = Path(TMP_DIR) / ".venv_repro"
REQUIREMENTS_FILE = Path(TMP_DIR) / "requirements.txt"


def get_venv_python_executable(venv_path: Path) -> Path:
    """Determines the path to the venv's Python executable based on the operating system."""
    if sys.platform.startswith('win'):
        return venv_path / "Scripts" / "python.exe"
    else:
        # Assumes Linux/macOS
        return venv_path / "bin" / "python"


def execute_subprocess(command: List[str], error_message: str):
    """Utility to run a subprocess command with check=True and custom error handling."""
    try:
        # check=True raises CalledProcessError if the command fails
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {error_message} (External command failed).", file=sys.stderr)
        # Print the error output for debugging
        print(f"Command: {' '.join(command)}", file=sys.stderr)
        print(f"Stderr:\n{e.stderr}", file=sys.stderr)
        raise RuntimeError(f"{error_message} failed.") from e
    except FileNotFoundError as e:
        print(f"[FATAL] System executable not found (e.g., 'python'): {e}", file=sys.stderr)
        raise RuntimeError(f"{error_message} failed.") from e
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        raise RuntimeError(f"{error_message} failed.") from e


def filter_requirements(requirements_file: Path) -> Path:
    """
    Loads the requirements file, filters out problematic dependencies (like 'ast' 
    which conflicts with the standard library and causes build failures), and 
    writes the filtered list to a temporary file for installation.
    
    Returns the path to the *new* filtered requirements file.
    """
    if not requirements_file.exists():
        return requirements_file # Nothing to filter

    print("[INFO] Filtering requirements.txt for known problematic packages...")
    
    # 'ast' causes FileNotFoundError during metadata generation.
    # 'enum34' is a common conflict on newer Python versions.
    packages_to_skip = {'ast', 'enum34'} 
    
    filtered_lines = []
    
    try:
        lines = requirements_file.read_text(encoding='utf-8').splitlines()
        for line in lines:
            # Clean up the line to get the package name before any version specifier
            # Use re.split to handle various separators (=, >, <, ~)
            package_name_parts = re.split(r'[=><~]', line.strip())
            package_name = package_name_parts[0].strip() if package_name_parts else ''
            
            # Skip comments and empty lines
            if not package_name or package_name.startswith('#'):
                continue
            
            if package_name not in packages_to_skip:
                filtered_lines.append(line)
                
    except Exception as e:
        print(f"[WARNING] Could not read or filter requirements file: {e}. Using original file.", file=sys.stderr)
        return requirements_file

    # Write filtered content to a new temporary file
    filtered_file = requirements_file.parent / "requirements_filtered.txt"
    try:
        filtered_file.write_text('\n'.join(filtered_lines), encoding='utf-8')
        print(f"[SUCCESS] Filtered dependencies written to: {filtered_file.name}")
        return filtered_file
    except Exception as e:
        print(f"[ERROR] Could not write filtered requirements file: {e}. Using original file.", file=sys.stderr)
        return requirements_file


def create_and_install_venv(repo_path: Path):
    """
    Creates a new virtual environment, upgrades core tools, and installs 
    dependencies from the pre-generated requirements.txt.
    """
    print(f"\n--- STEP 5: Setting up Virtual Environment in {VENV_DIR.name}... ---")
    
    # --- 5a. Create the Virtual Environment ---
    if VENV_DIR.exists():
        print(f"[INFO] Cleaning up existing Venv directory: {VENV_DIR.name}...")
        try:
            shutil.rmtree(VENV_DIR)
            print("[INFO] Venv directory cleaned.")
        except Exception as e:
            print(f"[WARNING] Could not remove Venv directory {VENV_DIR.name}: {e}")
            
    print(f"[INFO] Creating virtual environment at {VENV_DIR}...")
    execute_subprocess(
        [sys.executable, '-m', 'venv', str(VENV_DIR)],
        "Virtual environment creation"
    )
    print("[SUCCESS] Virtual environment created.")
    
    python_executable = get_venv_python_executable(VENV_DIR)

    # CRITICAL FIX STEP: Pre-install enum34 to satisfy broken build dependencies that look for '__version__'
    # This must run before upgrading pip/setuptools in case the base venv tools are also affected.

    # --- 5b. Upgrade Core Build Tools (Crucial fix for 'enum' error) ---
    print("[INFO] Upgrading pip, setuptools, and wheel in the virtual environment...")
    execute_subprocess(
        [str(python_executable), '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'],
        "Upgrade of core build tools"
    )
    print("[SUCCESS] Core build tools upgraded.")
    
    # Check if the original requirements file exists and is not empty
    if not REQUIREMENTS_FILE.exists() or REQUIREMENTS_FILE.stat().st_size == 0:
        print(f"[WARNING] Requirements file not found or is empty at {REQUIREMENTS_FILE.name}. Skipping dependency installation.")
        return

    # Filter out known problematic packages (like 'ast')
    requirements_to_install = filter_requirements(REQUIREMENTS_FILE)
        
    print(f"[INFO] Installing dependencies from {requirements_to_install.name} into Venv...")
    
    # Use a robust installation command
    install_command = [
        str(python_executable), 
        '-m', 
        'pip', 
        'install', 
        '--no-cache-dir', 
        '-r', 
        str(requirements_to_install), # <-- Use the filtered file path here
        '--no-build-isolation'
    ]

    execute_subprocess(
        install_command,
        "Final dependency installation"
    )
    
    print("[SUCCESS] All dependencies installed.")