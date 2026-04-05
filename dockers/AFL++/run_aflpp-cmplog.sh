#!/bin/bash
set -euo pipefail

MAZE_DIR=$1
PROGRAM_NAME=$2
TIMEOUT="${3}m"
MAZE_SIZE=$4
MAZE_TXT=$5
WORKDIR=/home/maze/workspace
TOOL_DIR=/home/maze/tools
IN_DIR="${WORKDIR}/inputs"
OUT_DIR="${WORKDIR}/outputs"

# ── Static analysis (ko-clang AFLGO distance preprocessing) ───────────────────
export MAZERUNNER_SRC=/workdir/symsan
export KO_CC=clang-12
export KO_CXX=clang++-12
export CC=$MAZERUNNER_SRC/build/bin/ko-clang
export CXX=$MAZERUNNER_SRC/build/bin/ko-clang++
export KO_USE_FASTGEN=1
export KO_ADD_AFLGO=1
export KO_DONT_OPTIMIZE=1
export BUILD_DIR=$WORKDIR/build
export AFLGO_TARGET_DIR=$BUILD_DIR/targets
export AFLGO_PREPROCESSING=1
mkdir -p $OUT_DIR $BUILD_DIR $AFLGO_TARGET_DIR

touch $WORKDIR/.sa_start
pushd $BUILD_DIR
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c ./file.c
ABORT_LINE=$(awk '/func_bug\(input/ { print NR }' file.c)
echo "file.c:$ABORT_LINE" > $AFLGO_TARGET_DIR/BBtargets.txt
# generate CFGs and call graph
$CC -g -o ${PROGRAM_NAME}_preprocessing ./file.c
# compute distances
python3 $MAZERUNNER_SRC/mazerunner/static_analysis.py $AFLGO_TARGET_DIR
unset AFLGO_PREPROCESSING
popd

# ── AFL++ compilation (normal + cmplog) ───────────────────────────────────────
export AFLPP="${TOOL_DIR}/AFLplusplus"
export CC="${AFLPP}/afl-clang-fast"
export CXX="${AFLPP}/afl-clang-fast++"
AFL_BIN="${BUILD_DIR}/${PROGRAM_NAME}_aflpp"
AFL_CMPLOG_BIN="${BUILD_DIR}/${PROGRAM_NAME}_aflpp_cmplog"
$CC -g -o $AFL_BIN ${MAZE_DIR}/src/${PROGRAM_NAME}.c
export AFL_LLVM_CMPLOG=1
$CC -g -o $AFL_CMPLOG_BIN ${MAZE_DIR}/src/${PROGRAM_NAME}.c
unset AFL_LLVM_CMPLOG
unset CC && unset CXX

# ── Seed directory & coverage counter ─────────────────────────────────────────
mkdir -p $IN_DIR
if [[ ! -f "${IN_DIR}/init" ]]; then
    python3 -c "print('A' * 1024)" > ${IN_DIR}/init
fi
COV_DIR="${OUT_DIR}/maze_cov"
mkdir -p "$COV_DIR"
export MAZE_COV="${COV_DIR}/accumulated_counter"
python3 -c "print('0\n' * ${MAZE_SIZE})" > $MAZE_COV

ulimit -c 0
# Create dummy file to indicate running start
touch $WORKDIR/.start

nohup timeout $TIMEOUT python3 ${TOOL_DIR}/visualize_maze_cov.py ${MAZE_DIR}/txt/${MAZE_TXT}.txt ${COV_DIR}/accumulated_counter $MAZE_SIZE ${OUT_DIR}/default/crashes > ${OUT_DIR}/visualize.log 2>&1 &
nohup timeout $TIMEOUT afl-fuzz -t 2000+ -m none -i $IN_DIR -o $OUT_DIR -c $AFL_CMPLOG_BIN -- $AFL_BIN > ${OUT_DIR}/aflpp.log 2>&1 &

# Wait for the timeout and mark done
sleep 1s
sleep $TIMEOUT && touch $WORKDIR/.done
