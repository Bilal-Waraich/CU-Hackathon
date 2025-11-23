import sys
import subprocess
from pathlib import Path
from typing import List
import shutil 

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
    print("[INFO] Attempting fix: Pre-installing 'enum34' to resolve recurrent build dependency errors...")
    execute_subprocess(
        [str(python_executable), '-m', 'pip', 'install', 'enum34'],
        "Pre-installation of enum34"
    )
    print("[SUCCESS] 'enum34' installed (attempting to patch build environment).")

    # --- 5b. Upgrade Core Build Tools (Crucial fix for 'enum' error) ---
    print("[INFO] Upgrading pip, setuptools, and wheel in the virtual environment...")
    execute_subprocess(
        [str(python_executable), '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'],
        "Upgrade of core build tools"
    )
    print("[SUCCESS] Core build tools upgraded.")

    # --- 5c. Check for requirements file and install dependencies ---
    
    if not REQUIREMENTS_FILE.exists() or REQUIREMENTS_FILE.stat().st_size == 0:
        print(f"[WARNING] Requirements file not found or is empty at {REQUIREMENTS_FILE}. Skipping dependency installation.")
        return
        
    print(f"[INFO] Installing dependencies from {REQUIREMENTS_FILE.name} into Venv...")
    
    # Use a robust installation command with --no-build-isolation
    install_command = [
        str(python_executable), 
        '-m', 
        'pip', 
        'install', 
        '--no-cache-dir', 
        '-r', 
        str(REQUIREMENTS_FILE),
        '--no-build-isolation',
        '--use-deprecated=legacy-resolver'
    ]
    
    execute_subprocess(
        install_command,
        "Final dependency installation"
    )
    
    print("[SUCCESS] All external dependencies installed successfully.")