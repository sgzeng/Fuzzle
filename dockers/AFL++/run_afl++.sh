#!/bin/bash
set -e

MAZE_DIR=$1
PROGRAM_NAME=$2
TIMEOUT="${3}m"
MAZE_SIZE=$4
MAZE_TXT=$5
WORKDIR=/home/maze/workspace
TOOL_DIR=/home/maze/tools
IN_DIR="${WORKDIR}/inputs"
OUT_DIR="${WORKDIR}/outputs"

# build the maze with afl++ instrumentation
if [[ ! -d "${MAZE_DIR}/build" ]]; then
    mkdir -p ${MAZE_DIR}/build
fi
export AFLPP="${TOOL_DIR}/AFLplusplus"
export CC="${AFLPP}/afl-clang-fast"
export CXX="${AFLPP}/afl-clang-fast++"
AFL_BIN="${MAZE_DIR}/build/${PROGRAM_NAME}_aflpp"
AFL_CMPLOG_BIN="${MAZE_DIR}/build/${PROGRAM_NAME}_aflpp_cmplog"
$CC -g -o $AFL_BIN ${MAZE_DIR}/src/${PROGRAM_NAME}.c
export AFL_LLVM_CMPLOG=1
$CC -g -o $AFL_CMPLOG_BIN ${MAZE_DIR}/src/${PROGRAM_NAME}.c
unset AFL_LLVM_CMPLOG
unset CC && unset CXX

# create initial seed directory
mkdir -p $IN_DIR
if [[ ! -d "$IN_DIR" ]] || [[ ! -f "${IN_DIR}/init" ]]; then
    mkdir -p $IN_DIR
    python3 -c "print('A' * 1024)" > ${IN_DIR}/init
fi
# create coverage tracing directory
COV_DIR="${OUT_DIR}/maze_cov"
mkdir -p "$COV_DIR"
export MAZE_COV="${COV_DIR}/accumulated_counter"
python3 -c "print('0\n' * ${MAZE_SIZE})" > $MAZE_COV

ulimit -c 0
# Create dummy file to indicate running start
touch $WORKDIR/.start

nohup timeout $TIMEOUT python3 ${TOOL_DIR}/visualize_maze_cov.py ${MAZE_DIR}/txt/${MAZE_TXT}.txt ${COV_DIR}/accumulated_counter $MAZE_SIZE > ${OUT_DIR}/visualize.log 2>&1 &
nohup timeout $TIMEOUT afl-fuzz -t 2000+ -m none -i $IN_DIR -o $OUT_DIR -c $AFL_CMPLOG_BIN -- $AFL_BIN > ${OUT_DIR}/aflpp.log 2>&1 &
