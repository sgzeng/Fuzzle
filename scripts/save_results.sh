#!/bin/bash

# Usage: save_results.sh <FUZZ_OUT> <EXPERIMENT.conf> <PARAM> <DURATION_h> [MODE]
# EXPERIMENT.conf: same JSON as run_tools.py (MazeList, MazeDir, Tools, …) — save_results.py reads MazeDir.
# PARAM: Algorithm | Size | Cycle | Generator
FUZZ_OUTPUT=$(readlink -f "$1")
CONFIG=$(readlink -f "$2")
PARAM=$3
DURATION=$4
MODE_PAPER=${5:-paper}
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

MODE=$MODE_PAPER
for dir in "$FUZZ_OUTPUT"/*; do
    if [ -d "$dir" ]; then
        MAZE_OUTPUT="$dir"
        python3 "$SCRIPT_DIR/save_results.py" "$MAZE_OUTPUT" "$CONFIG" "$PARAM" "$DURATION" "$MODE" &> "$MAZE_OUTPUT/summary_${MODE}_${DURATION}h.txt"
    fi
done

MODE=fuzzer
python3 "$SCRIPT_DIR/save_results.py" "$FUZZ_OUTPUT" "$CONFIG" "$PARAM" "$DURATION" "$MODE" &> "$FUZZ_OUTPUT/summary_${MODE}_${DURATION}h.md"
python3 "$SCRIPT_DIR/gen_table.py" "$FUZZ_OUTPUT/summary_${MODE}_${DURATION}h.md"
# python3 "$SCRIPT_DIR/gen_visualization.py" "$FUZZ_OUTPUT" "$CONFIG" "$PARAM" "$DURATION" "$MODE"
echo "[*] done!"
