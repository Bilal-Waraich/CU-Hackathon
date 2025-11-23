import os
import shutil
import subprocess
import time
import stat
from typing import Optional
import urllib.request
from pathlib import Path

class Downloader:
    """
    A utility class to clone a GitHub repository and download PDFs.

    It provides functionality to clone into a specified target path (which
    is essential for separating 'tmp' and 'workspace' clones).
    """
    
    def __init__(self, target_dir: str = "tmp", max_retries: int = 5, retry_delay: float = 1.0):
        # target_dir is primarily used for PDF downloads and default cleanup
        self.target_dir = target_dir
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _cleanup_error_handler(self, func, path, exc_info):
        """
        Custom error handler for shutil.rmtree to handle Windows permission errors.
        (Retained and used for robust directory deletion)
        """
        # The exception type is often PermissionError (a subclass of OSError) on WinError 5
        if issubclass(exc_info[0], PermissionError) or issubclass(exc_info[0], OSError):
            # Attempt to change file permissions to allow writing/deleting
            os.chmod(path, stat.S_IWUSR | stat.S_IWRITE)
            
            try:
                # Retry the removal function
                func(path)
                return  
            except Exception:
                # If retry fails, let the error propagate 
                pass 
        
        # If not a recognized cleanup error, or if retry failed, raise the original exception
        raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
    
    def _cleanup_single_dir(self, directory: str) -> bool:
        """Removes a single directory robustly using the error handler."""
        path = Path(directory)
        if not path.exists():
            return True

        print(f"Cleaning up existing directory: '{path}'...")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                shutil.rmtree(path, onerror=self._cleanup_error_handler)
                print(f"Directory '{path}' successfully deleted on attempt {attempt}.")
                return True
            except Exception as e:
                if attempt < self.max_retries:
                    print(f"Cleanup attempt {attempt} failed: {type(e).__name__} - {e}. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Error during directory cleanup after {self.max_retries} attempts: {e}")
                    raise 
        return False

    def download(self, github_link: str, target_path: str, branch: Optional[str] = None) -> bool:
        """
        Clones the specified GitHub repository into the target_path.
        
        CRITICAL FIX: The target_path argument is now used as the destination in the git command.
        """
        
        # We perform cleanup *before* cloning, targeting the specific destination path.
        try:
            # We use the target_path provided by main.py for cleanup
            self._cleanup_single_dir(target_path) 
        except Exception:
            return False

        print(f"Attempting to clone '{github_link}' into '{target_path}'...")

        command = ['git', 'clone']
        
        if branch:
            command.extend(['--branch', branch])
        
        # CRITICAL FIX: Use the flexible target_path provided by main.py
        command.extend([github_link, target_path])

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            print("Cloning successful.")
            print(f"Output:\n{result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n--- ERROR DURING GIT CLONE ---")
            print(f"Command failed with exit code {e.returncode}: {' '.join(command)}")
            print(f"STDERR:\n{e.stderr}")
            print(f"------------------------------")
            return False
        except FileNotFoundError:
            print("\n--- ERROR: GIT NOT FOUND ---")
            print("The 'git' command was not found. Please ensure Git is installed and added to your system's PATH.")
            print("------------------------------")
            return False
        
    def download_pdf(self, pdf_url: str, output_path: Optional[str] = None) -> bool:
        """
        Download a PDF from the given URL and save it locally.

        If `output_path` is not provided, the file is saved under `self.target_dir`
        using the filename inferred from the URL (or 'downloaded.pdf' as fallback).
        """

        target_dir_path = Path(self.target_dir)
        target_dir_path.mkdir(parents=True, exist_ok=True)

        if output_path is None:
            filename = os.path.basename(pdf_url.split("?", 1)[0])  
            if not filename.lower().endswith(".pdf") or not filename:
                filename = "downloaded.pdf"

            output_path = str(target_dir_path / filename)

        print(f"Attempting to download PDF from '{pdf_url}' to '{output_path}'...")

        for attempt in range(1, self.max_retries + 1):
            try:
                # Use urllib.request as per original user code
                with urllib.request.urlopen(pdf_url) as response:
                    if response.status != 200:
                        raise OSError(f"HTTP status {response.status}")

                    with open(output_path, "wb") as f:
                        shutil.copyfileobj(response, f)

                print(f"PDF successfully downloaded on attempt {attempt}.")
                return True

            except Exception as e:
                if attempt < self.max_retries:
                    print(
                        f"Download attempt {attempt} failed: "
                        f"{type(e).__name__} - {e}. Retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    print(
                        f"Error downloading PDF after {self.max_retries} attempts: {e}"
                    )
                return False