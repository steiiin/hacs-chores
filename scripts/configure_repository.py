"""Fill owner and repository metadata before publishing to GitHub."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument("repository", help="OWNER/REPOSITORY, e.g. your-name/hacs-chores")
args = parser.parse_args()
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", args.repository):
    parser.error("Expected OWNER/REPOSITORY")
root = Path(__file__).resolve().parents[1]
path = root / "custom_components/hacs_chores/manifest.json"
manifest = json.loads(path.read_text())
manifest.update(codeowners=["@" + args.repository.split('/')[0]],
                documentation="https://github.com/" + args.repository,
                issue_tracker="https://github.com/" + args.repository + "/issues")
path.write_text(json.dumps(manifest, indent=2) + "\n")
print("Repository metadata updated in", path)
