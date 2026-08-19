#!/usr/bin/env bash
# Upload a WorldRover release to the Hugging Face Hub, one dataset repo per scene.
#
#   pip install -U "huggingface_hub[hf_transfer]"
#   hf auth login                      # write-scoped token
#   bash scripts/upload_to_hf.sh /data/WorldRover AlayaLab
#
# One repo per scene keeps every repo inside the Hub's recommended size (each scene is
# 170-290 GB, the whole release is ~800 GB). `upload-large-folder` is resumable: rerun
# the same command after an interruption and it continues.
set -euo pipefail

ROOT=${1:?usage: upload_to_hf.sh <dataset_root> <hf_org> [scene ...]}
ORG=${2:?usage: upload_to_hf.sh <dataset_root> <hf_org> [scene ...]}
shift 2
SCENES=("$@")
if [ ${#SCENES[@]} -eq 0 ]; then
  SCENES=(med_village paris venice art_nouveau)
fi

export HF_HUB_ENABLE_HF_TRANSFER=1     # multi-threaded transfer; big win on fat pipes

for scene in "${SCENES[@]}"; do
  [ -d "$ROOT/$scene" ] || { echo "skip $scene (not in $ROOT)"; continue; }
  repo="$ORG/WorldRover-$scene"
  echo "=== $repo <- $ROOT/$scene"
  hf repo create "$repo" --repo-type dataset --exist-ok
  # the card lives at the repo root; scene folders keep pano/ and fp/ side by side
  hf upload-large-folder "$repo" "$ROOT/$scene" --repo-type dataset --num-workers 8
done

echo
echo "Now upload the dataset card to each repo (edit hf/DATASET_CARD.md first):"
for scene in "${SCENES[@]}"; do
  echo "  hf upload $ORG/WorldRover-$scene hf/DATASET_CARD.md README.md --repo-type dataset"
done
