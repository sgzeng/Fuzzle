#!/bin/bash
# Full pipeline: generate → docker fuzz → summarize → visualize.
# Post-processing only (reuse outputs under test_output/): FUZZLE_TEST_POST_ONLY=1 ./test.sh
set -eu

OUT_PATH=$(readlink -f "$(dirname "$0")")/test_output
CONFIG_DIR=$(readlink -f "$(dirname "$0")")/test_config
SCRIPT_DIR=$(readlink -f "$(dirname "$0")/..")/scripts
mkdir -p "$OUT_PATH"
OUT_TEST="$OUT_PATH/outputs"

cd "$SCRIPT_DIR"

if [ "${FUZZLE_TEST_POST_ONLY:-0}" != 1 ]; then
    if [ -d "$OUT_TEST" ]; then
        rm -rf "$OUT_TEST"
    fi
	python3 ./generate_benchmark.py "$CONFIG_DIR/test.list" "$OUT_PATH/test_benchmark"
	python3 ./run_tools.py "$CONFIG_DIR/test.conf" "$OUT_TEST"
fi

# Second arg must be the same JSON as run_tools.py (save_results.py loads MazeDir / MazeList).
./save_results.sh "$OUT_TEST" "$CONFIG_DIR/test.conf" Generator 0 paper >"$OUT_PATH/test_summary"
# Tables are written per-maze under outputs/*/summary_paper_<DURATION>h.txt
for f in "$OUT_TEST"/*/summary_paper_0h.txt; do
	[ -f "$f" ] || continue
	echo "--- $f ---" >>"$OUT_PATH/test_summary"
	cat "$f" >>"$OUT_PATH/test_summary"
done

# Gcov layout: outputs/<put>/cov_gcov_<put>_<tool>_<epoch>/<put>_<tool>_<epoch>.c.gcov
PUT=Wilsons_20x20_1_1_25percent_CVE-2016-6131_gen
TOOL=mazerunner-exploit-max
EPOCH=0
PATH_TO_TXT="$OUT_PATH/test_benchmark/txt/Wilsons_20x20_1_1.txt"
PATH_TO_COV="$OUT_TEST/$PUT/cov_gcov_${PUT}_${TOOL}_${EPOCH}/${PUT}_${TOOL}_${EPOCH}.c.gcov"
if [ ! -f "$PATH_TO_COV" ]; then
	PATH_TO_COV=$(find "$OUT_TEST" -name '*.gcov' -print -quit || true)
fi
if [ -z "$PATH_TO_COV" ] || [ ! -f "$PATH_TO_COV" ]; then
	echo "No .gcov under $OUT_TEST; run full pipeline without FUZZLE_TEST_POST_ONLY=1" >&2
	exit 1
fi
python3 ./visualize.py "$PATH_TO_TXT" "$PATH_TO_COV" "$OUT_PATH/visual" 20

cat "$OUT_PATH/test_summary"
