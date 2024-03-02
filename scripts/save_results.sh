#!/bin/bash
set -e
set -x

FUZZ_OUTPUT=$1
CONFIG=$2
PARAM=Generator
DURATION=$3
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

MODE=paper
for dir in "$FUZZ_OUTPUT"/*; do
    if [ -d "$dir" ]; then
        MAZE_OUTPUT="$dir"
        python3 "$SCRIPT_DIR/save_results.py" "$MAZE_OUTPUT" "$CONFIG" "$PARAM" "$DURATION" "$MODE" &> "$MAZE_OUTPUT/summary_${MODE}_${DURATION}h.txt"
    fi
done

MODE=fuzzer
python3 "$SCRIPT_DIR/save_results.py" "$FUZZ_OUTPUT" "$CONFIG" "$PARAM" "$DURATION" "$MODE" &> "$FUZZ_OUTPUT/summary_${MODE}_${DURATION}h.md"
python3 "$SCRIPT_DIR/gen_table.py" "$FUZZ_OUTPUT/summary_${MODE}_${DURATION}h.md"
