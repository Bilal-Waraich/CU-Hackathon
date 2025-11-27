from __future__ import annotations
from typing import List
from math import random

from pathlib import Path

# --------------------------------- # 
# batch eval testing constant 
# --------------------------------- # 


ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = ROOT / "src" / "main.py"

TMP_DIR = ROOT / "tmp"
REPO_DIR = TMP_DIR / "repo"
VENV_DIR = TMP_DIR / ".venv_repro"
WORKSPACE_DIR = ROOT / "workspace"

DEMO_FILENAME = "generated_demo.py"

LOG_DIR = ROOT / "batch_logs"
RESULTS_CSV = ROOT / "batch_results.csv"
RESULTS_JSON = ROOT / "batch_results.json"
SUMMARY_TXT = ROOT / "batch_summary.txt"

PIPELINE_TIMEOUT = 600  
DEMO_TIMEOUT = 120     



ALL_PAPER_URLS: List[str] = [
    "https://arxiv.org/pdf/2203.14090",
    "https://arxiv.org/pdf/1907.10902",
    "https://arxiv.org/pdf/1802.03426",
    "https://arxiv.org/pdf/2207.12274",
    "https://genomebiology.biomedcentral.com/counter/pdf/10.1186/s13059-017-1382-0.pdf",
    "https://arxiv.org/pdf/2406.07817",
    "https://www.theoj.org/joss-papers/joss.07975/10.21105.joss.07975.pdf",
    "https://arxiv.org/pdf/2103.16196v2",
    "https://arxiv.org/pdf/2307.08234v2",
    "https://arxiv.org/pdf/2507.06825",
    "https://arxiv.org/pdf/2506.01192",
    "https://arxiv.org/pdf/2506.01151",
    "https://arxiv.org/pdf/2507.07257",
    "https://arxiv.org/pdf/2507.07101",
    "https://arxiv.org/pdf/2507.06849",
    "https://arxiv.org/pdf/2507.06219",
    "https://arxiv.org/pdf/2507.04127",
    "https://arxiv.org/pdf/2507.03009",
    "https://arxiv.org/pdf/2506.23825",
    "https://arxiv.org/pdf/2506.21182",
    "https://arxiv.org/pdf/2506.19398",
    "https://arxiv.org/pdf/2506.14965",
    "https://arxiv.org/pdf/2506.12494",
    "https://arxiv.org/pdf/2506.09081",
    "https://arxiv.org/pdf/2506.08889",
    "https://arxiv.org/pdf/2506.03887",
    "https://arxiv.org/pdf/2506.01853",
    "https://arxiv.org/pdf/2506.01822",
    "https://arxiv.org/pdf/2506.01268",
    "https://arxiv.org/pdf/2505.23313",
    "https://arxiv.org/pdf/2505.22296",
    "https://arxiv.org/pdf/2505.21297",
    "https://arxiv.org/pdf/2505.20414",
    "https://arxiv.org/pdf/2505.18582",
    "https://arxiv.org/pdf/2505.17756",
    "https://arxiv.org/pdf/2505.15307",
    "https://arxiv.org/pdf/2505.15155",
    "https://arxiv.org/pdf/2505.13307",
    "https://arxiv.org/pdf/2505.12668",
    "https://arxiv.org/pdf/2505.03336",
    "https://arxiv.org/pdf/2505.02395",
    "https://arxiv.org/pdf/2505.01257",
    "https://arxiv.org/pdf/2504.20073",
    "https://arxiv.org/pdf/2504.15329",
    "https://arxiv.org/pdf/2504.14603",
    "https://arxiv.org/pdf/2504.13934",
    "https://arxiv.org/pdf/2504.13619",
    "https://arxiv.org/pdf/2504.20650",
    "https://arxiv.org/pdf/2504.10591",
    "https://arxiv.org/pdf/2504.09975",
    "https://arxiv.org/pdf/2504.08339",
    "https://arxiv.org/pdf/2504.07439",
    "https://arxiv.org/pdf/2504.07091",
    "https://arxiv.org/pdf/2504.00906",
    "https://arxiv.org/pdf/2504.00882",
    "https://arxiv.org/pdf/2503.22673",
    "https://arxiv.org/pdf/2503.20563",
    "https://arxiv.org/pdf/2503.20068",
    "https://arxiv.org/pdf/2503.17076",
    "https://arxiv.org/pdf/2503.15621",
    "https://arxiv.org/pdf/2503.15438",
    "https://arxiv.org/pdf/2503.12340",
    "https://arxiv.org/pdf/2503.11509",
    "https://arxiv.org/pdf/2503.11070",
    "https://arxiv.org/pdf/2503.10284",
    "https://arxiv.org/pdf/2503.09642",
    "https://arxiv.org/pdf/2503.09033",
    "https://arxiv.org/pdf/2503.08373",
    "https://arxiv.org/pdf/2503.08354",
    "https://arxiv.org/pdf/2503.07465",
    "https://arxiv.org/pdf/2503.07091",
    "https://arxiv.org/pdf/2503.07029",
    "https://arxiv.org/pdf/2503.06252",
    "https://arxiv.org/pdf/2503.05447",
    "https://arxiv.org/pdf/2503.04548",
    "https://arxiv.org/pdf/2503.04065",
    "https://arxiv.org/pdf/2503.03669",
    "https://arxiv.org/pdf/2503.02950",
    "https://arxiv.org/pdf/2503.01840",
    "https://arxiv.org/pdf/2503.01461",
    "https://arxiv.org/pdf/2502.20762",
    "https://arxiv.org/pdf/2502.20272",
    "https://arxiv.org/pdf/2502.20110",
    "https://arxiv.org/pdf/2502.19854",
    "https://arxiv.org/pdf/2502.19209",
    "https://arxiv.org/pdf/2502.18834",
    "https://arxiv.org/pdf/2502.18807",
    "https://arxiv.org/pdf/2502.16776",
    "https://arxiv.org/pdf/2502.15824",
    "https://arxiv.org/pdf/2502.15589",
    "https://arxiv.org/pdf/2502.13785",
    "https://arxiv.org/pdf/2502.13716",
    "https://arxiv.org/pdf/2502.10470",
    "https://arxiv.org/pdf/2502.09390",
    "https://arxiv.org/pdf/2502.07972",
    "https://arxiv.org/pdf/2502.05505",
]


STEP_MARKERS = {
    1: "--- STEP 1:",
    2: "--- STEP 2:",
    3: "--- STEP 3:",
    4: "--- STEP 4:",
    5: "--- STEP 5:",
    6: "--- STEP 6:",
    7: "--- STEP 7:",
}

STEP_NAMES = {
    0: "No steps completed",
    1: "PDF Download/Loading",
    2: "GitHub URL Extraction",
    3: "Repository Cloning",
    4: "Dependency Extraction",
    5: "Virtual Environment Setup",
    6: "Demo Generation",
    7: "Demo Execution",
}