import subprocess
from typing import Set
import os
import shutil



def get_installed_packages(venv_python: str) -> Set[str]:
    """
    Get a set of installed package names from the virtual environment.
    """
    try:
        result = subprocess.run(
            [venv_python, "-m", "pip", "list", "--format=freeze"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return set()
        
        packages: Set[str] = set()
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                pkg_name = line.split('==')[0].strip().lower()
                packages.add(pkg_name)
            elif line.strip():
                packages.add(line.strip().lower())
        
        return packages
        
    except Exception:
        return set()


def clone_repository(github_url: str, target_dir: str) -> bool:
    """
    Clone a GitHub repository to the target directory.
    """
    print(f"Attempting to clone '{github_url}' into '{target_dir}'...")
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", github_url, target_dir],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("Cloning successful.")
            return True
        else:
            print(f"[ERROR] Git clone failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Git clone timed out after 300 seconds.")
        return False
    except FileNotFoundError:
        print("[ERROR] Git is not installed or not in PATH.")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error during clone: {e}")
        return False


def run_demo(venv_python: str, demo_path: str, repo_path: str) -> bool:
    """
    Execute the generated demo script.
    """
    print(f"\n--- Running Demo: {demo_path} ---")
    
    try:
        result = subprocess.run(
            [venv_python, demo_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        print("Demo Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Demo Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("[SUCCESS] Demo completed successfully!")
            return True
        else:
            print(f"[WARNING] Demo exited with code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Demo timed out after 600 seconds.")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run demo: {e}")
        return False
