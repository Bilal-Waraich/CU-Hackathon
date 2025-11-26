"""
main.py - Scientific Code Reproducibility Pipeline

This is the main entry point for the Repoduce-Me pipeline that:
1. Downloads a PDF from URL or uses a local PDF
2. Parses the PDF to extract GitHub repository URL
3. Clones the GitHub repository
4. Extracts and installs dependencies in a virtual environment
5. Generates a runnable demo script using an LLM
6. Optionally executes the demo
"""

import os
import sys
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Set

from downloader import Downloader
from paper_extracter import PaperParser
from requirements_extract import RequirementsExtractor
from venv_create import setup_venv_and_install, get_venv_python
from demo_creator import DemoCreator

from utils import get_installed_packages, clone_repository, run_demo

from constants import (
    TMP_DIR, 
    WORKSPACE_DIR,
    DEMO_FILENAME
)

def main():
    parser = argparse.ArgumentParser(
        description="Repoduce-Me: Scientific Code Reproducibility Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            python main.py https://arxiv.org/pdf/2207.12274
            python main.py paper.pdf --github https://github.com/owner/repo
            python main.py paper.pdf --tmp --auto-run
        """
    )
    
    parser.add_argument(
        "input",
        help="ArXiv URL, PDF URL, or local path to a research paper PDF"
    )
    parser.add_argument(
        "--github",
        help="Explicit GitHub repository URL (skips PDF parsing)"
    )
    parser.add_argument(
        "--tmp",
        action="store_true",
        help="Use ephemeral tmp/ directory instead of workspace/"
    )
    parser.add_argument(
        "--auto-run",
        action="store_true",
        help="Automatically run the generated demo after creation"
    )
    parser.add_argument(
        "--skip-demo",
        action="store_true",
        help="Skip demo generation (only setup environment)"
    )
    parser.add_argument(
        "--python",
        default=None,
        help="Python executable to use for creating the virtual environment"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up temporary files on failure"
    )
    
    args = parser.parse_args()
    
    work_dir = TMP_DIR if args.tmp else WORKSPACE_DIR
    
    os.makedirs(work_dir, exist_ok=True)
    
    work_dir_abs = os.path.abspath(work_dir)
    repo_dir = os.path.join(work_dir_abs, "repo")
    venv_dir = os.path.join(work_dir_abs, ".venv_repro")
    
    demo_path = os.path.join(repo_dir, DEMO_FILENAME)
    
    print(f"\n--- Starting Pipeline Execution with Input: {args.input} ---")
    
    try:
        # ============================================================
        # STEP 1: Resolve input to local PDF
        # ============================================================
        input_path = args.input
        
        if input_path.startswith(('http://', 'https://')):
            print("--- STEP 1: Input is a URL. Downloading PDF... ---")
            
            downloader = Downloader(target_dir=work_dir_abs)
            pdf_path = os.path.join(work_dir_abs, "downloaded_paper.pdf")
            
            success = downloader.download_pdf(input_path, pdf_path)
            if not success:
                raise RuntimeError(f"Failed to download PDF from {input_path}")
            print(f"PDF successfully downloaded on attempt 1.\n")
        else:
            print("--- STEP 1: Input is a local file. ---")
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"PDF file not found: {input_path}")
            pdf_path = os.path.abspath(input_path)
            print(f"[INFO] Using local PDF: {pdf_path}\n")
        
        # ============================================================
        # STEP 2: Extract GitHub URL from PDF (or use provided URL)
        # ============================================================
        print("--- STEP 2: Parsing PDF for GitHub Repository URL... ---")
        
        if args.github:
            github_url = args.github
            print(f"[INFO] Using provided GitHub URL: {github_url}")
        else:
            # Create parser with the PDF path
            paper_parser = PaperParser(pdf_path)
            github_links = paper_parser.extract_github_link()
            
            if not github_links:
                raise RuntimeError("Could not find GitHub URL in the PDF")
            
            # Use the first found link
            github_url = github_links[0]
        
        print(f"[SUCCESS] Found GitHub URL: {github_url}\n")
        
        # ============================================================
        # STEP 3: Clone the repository
        # ============================================================
        print("--- STEP 3: Cloning GitHub Repository... ---")
        
        if not clone_repository(github_url, repo_dir):
            raise RuntimeError(f"Failed to clone repository: {github_url}")
        
        print(f"[SUCCESS] Repository successfully cloned into: {repo_dir}\n")
        
        # ============================================================
        # STEP 4: Analyze dependencies (informational)
        # ============================================================
        print("--- STEP 4: Dependency Extraction using RequirementsExtractor... ---")
        
        try:
            extractor = RequirementsExtractor(repo_dir=repo_dir, output_dir=work_dir_abs)
            deps = extractor.extract()
            
            if deps:
                if deps[0] == "__USE_PYPROJECT__":
                    print("[INFO] pyproject.toml detected - installation will be handled via pip install .")
                elif deps[0] == "__USE_SETUPTOOLS__":
                    print("[INFO] setup.py/setup.cfg detected - installation will be handled via pip install .")
                else:
                    print(f"[INFO] Found {len(deps)} dependencies.")
        except Exception as e:
            print(f"[WARNING] Dependency analysis failed: {e}")
            # Check for pyproject.toml manually
            pyproject_path = os.path.join(repo_dir, "pyproject.toml")
            if os.path.exists(pyproject_path):
                print("[INFO] pyproject.toml detected - installation will be handled via pip install .")
        
        print()
        
        # ============================================================
        # STEP 5: Create virtual environment and install dependencies
        # ============================================================
        print(f"--- STEP 5: Setting up Virtual Environment in {venv_dir}... ---")
        
        success, venv_python = setup_venv_and_install(
            venv_path=venv_dir,
            repo_path=repo_dir,
            python_executable=args.python,
            preinstall_deps=["numpy", "scipy"]
        )
        
        if not success:
            raise RuntimeError("Failed to setup virtual environment and install dependencies")
        
        print(f"\n[SUCCESS] Virtual environment ready with Python at: {venv_python}\n")
        
        # ============================================================
        # STEP 6: Generate demo (unless skipped)
        # ============================================================
        demo_generated = False
        
        if not args.skip_demo:
            print("--- STEP 6: Generating Demo Script... ---")
            
            try:
                installed_packages = get_installed_packages(venv_python)
                
                creator = DemoCreator(
                    repo_path=repo_dir,
                    output_filename=DEMO_FILENAME,
                    installed_packages=installed_packages
                )
                
                # Generate the demo
                result_path = creator.generate_demo()
                
                if result_path and Path(result_path).exists():
                    demo_generated = True
                    demo_path = str(result_path)
                    print(f"[SUCCESS] Demo script generated at: {demo_path}\n")
                else:
                    print("[WARNING] Demo generation failed or was skipped.\n")
                    
            except Exception as e:
                print(f"[WARNING] Demo generation failed: {e}\n")
                import traceback
                traceback.print_exc()
        else:
            print("--- STEP 6: Skipping Demo Generation (--skip-demo) ---\n")
        
        # ============================================================
        # STEP 7: Auto-run demo if requested
        # ============================================================
        if args.auto_run and demo_generated and os.path.exists(demo_path):
            print("--- STEP 7: Auto-Running Generated Demo... ---")
            run_demo(venv_python, demo_path, repo_dir)
        elif args.auto_run:
            print("--- STEP 7: Skipping Auto-Run (no demo available) ---\n")
        
        # ============================================================
        # Success summary
        # ============================================================
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"  Repository: {repo_dir}")
        print(f"  Virtual Environment: {venv_dir}")
        print(f"  Venv Python: {venv_python}")
        if demo_generated:
            print(f"  Demo Script: {demo_path}")
        print()
        print("To activate the environment:")
        if os.name == 'nt':
            print(f"  {venv_dir}\\Scripts\\activate")
        else:
            print(f"  source {venv_dir}/bin/activate")
        print("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}")
        return 1
    except RuntimeError as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n[INFO] Pipeline interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
