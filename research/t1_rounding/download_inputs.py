"""Download pinned official inputs; no model calls or hypothesis measurement."""
from pathlib import Path
import json
import urllib.request

HERE = Path(__file__).resolve().parent
FINQA_REV = "0f16e2867befa6840783e58be38c9efb9229d742"
TATQA_REV = "870accc41953dcde885aabeb963d94aabdc0fbc3"

def download(repo, revision, remote, local):
    target = HERE / "data" / local
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://raw.githubusercontent.com/{repo}/{revision}/{remote}"
    if target.exists():
        print(f"Already present: {local}")
        return
    request = urllib.request.Request(url, headers={"User-Agent": "T1-research-input-downloader"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if target.suffix == ".json":
        parsed = json.loads(payload)
        print(f"{local}: {len(parsed)} top-level entries, {len(payload)} bytes")
    else:
        print(f"{local}: {len(payload)} bytes")
    target.write_bytes(payload)

if __name__ == "__main__":
    for split in ["dev", "test", "train"]:
        download("czyssrs/FinQA", FINQA_REV, f"dataset/{split}.json", f"finqa/{split}.json")
    download("czyssrs/FinQA", FINQA_REV, "LICENSE", "finqa/LICENSE")
    download("czyssrs/FinQA", FINQA_REV, "code/evaluate/evaluate.py", "finqa/evaluate.py")
    download("NExTplusplus/TAT-QA", TATQA_REV, "dataset_raw/tatqa_dataset_dev.json", "tatqa/dev.json")
    download("NExTplusplus/TAT-QA", TATQA_REV, "LICENSE", "tatqa/LICENSE")
    download("NExTplusplus/TAT-QA", TATQA_REV, "tatqa_metric.py", "tatqa/tatqa_metric.py")
    download("NExTplusplus/TAT-QA", TATQA_REV, "tatqa_utils.py", "tatqa/tatqa_utils.py")
