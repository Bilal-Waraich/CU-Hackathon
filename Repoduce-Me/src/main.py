import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Configuration
# Define the temporary directory where files will be processed and repositories cloned.
# This path is used by the Downloader class's __init__ method by default.
TMP_DIR = "tmp"
PDF_OUTPUT_FILENAME = Path(TMP_DIR) / "downloaded_paper.pdf"

from downloader import Downloader
from paper_extracter import PaperParser

def create_demo_from_readme(repo_path: Path):
    """
    Placeholder for the script that creates a demo from the cloned repository's README.
    It should take the local path to the cloned repository as input.
    """
    print(f"\n--- STEP 4: Creating Demo from Readme... ---")
    if repo_path and repo_path.is_dir():
        # Add your demo creation logic here, e.g.,
        # DemoCreator(repo_path).generate_example()
        print(f"[INFO] Successfully called demo creation logic for: {repo_path}")
    else:
        print("[WARNING] Skipping demo creation: Repository path is invalid or clone failed.")


def run_pipeline(input_path: str):
    """
    The main orchestration function for the pipeline.
    """

    downloader = Downloader(target_dir=TMP_DIR)

    pdf_path: Optional[Path] = None
    
    try:
        if input_path.lower().startswith('http'):
            print("--- STEP 1: Input is a URL. Downloading PDF... ---")

            if downloader.download_pdf(input_path, str(PDF_OUTPUT_FILENAME)):
                pdf_path = PDF_OUTPUT_FILENAME
            else:
                raise ConnectionError(f"Failed to download PDF from: {input_path}")
        else:
            print("--- STEP 1: Input is a local PDF file. Skipping download... ---")

            pdf_path = Path(input_path)
            if not pdf_path.is_file():
                raise FileNotFoundError(f"Local file not found at: {pdf_path}")
            print(f"[INFO] Using local PDF file: {pdf_path}")

        # Ensure we have a path before proceeding
        if not pdf_path:
             raise ValueError("PDF file path could not be determined.")

        print("\n--- STEP 2: Parsing PDF for GitHub Repository URL... ---")
        
        github_links: list[str] = PaperParser(str(pdf_path)).extract_github_link()
        
        if not github_links:
            print("[WARNING] No GitHub link found in the paper. Pipeline stops.")
            return

        # Use the first link found (you might add logic here to choose the best one)
        github_url = github_links[0]
        print(f"[SUCCESS] Found GitHub URL: {github_url}")

        # STEP 3: Cloning GitHub Repository
        print("\n--- STEP 3: Cloning GitHub Repository... ---")

        # The downloader uses its 'target_dir' (TMP_DIR) for cloning.
        # downloader.download returns True/False for success.
        clone_success = downloader.download(github_url)
        cloned_repo_path = Path(TMP_DIR) # The repository is cloned into TMP_DIR

        if not clone_success:
            raise RuntimeError(f"Git clone failed for repository: {github_url}")
        
        print(f"[SUCCESS] Repository successfully cloned into: {cloned_repo_path}")

        # STEP 4: Demo Creation
        create_demo_from_readme(cloned_repo_path)

    # --- Error Handling ---
    except FileNotFoundError as e:
        print(f"[ERROR] Required file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ConnectionError as e:
        print(f"[ERROR] Network operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] Data validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"[ERROR] External command execution failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch any remaining unexpected errors
        print(f"[FATAL] An unexpected error occurred: {type(e).__name__} - {e}", file=sys.stderr)
        sys.exit(1)
        
    finally:
        # The Downloader's cleanup happens *before* cloning in `downloader.download()`.
        # If you want cleanup *after* the entire pipeline runs, you would add that logic here.
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A pipeline orchestrator for processing research papers (URL or PDF) to generate code demos."
    )
    parser.add_argument(
        "input",
        type=str,
        help="The input source, which can be either a full URL (e.g., http://arxiv.org/...) or a local path to a PDF file (e.g., ./paper.pdf)."
    )
    
    args = parser.parse_args()
    
    print(f"\n--- Starting Pipeline Execution with Input: {args.input} ---")
    
    # Start timing
    start_time = time.time()
    
    run_pipeline(args.input)
    
    # End timing and report duration
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n--- Pipeline Complete in {duration:.2f} seconds. ---")
    
    # Example of how to run this script from the command line:
    # python main.py "http://example.com/paper.pdf"
    # python main.py "./local_paper.pdf"