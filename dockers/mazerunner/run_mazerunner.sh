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

# create initial seed directory
if [[ ! -d "$IN_DIR" ]] || [[ ! -f "${IN_DIR}/init" ]]; then
    mkdir -p $IN_DIR
    python3 -c "print('A' * 2048)" > ${IN_DIR}/init
fi

export BUILD_DIR=$WORKDIR/build
export MAZERUNNER_SRC=/workdir/symsan
export KO_CXX=clang++-12
export KO_CC=clang-12
export CXX=$MAZERUNNER_SRC/build/bin/ko-clang++
export CC=$MAZERUNNER_SRC/build/bin/ko-clang
export KO_USE_FASTGEN=1
export KO_ADD_AFLGO=1
export AFLGO_TARGET_DIR=$BUILD_DIR/targets
export AFLGO_PREPROCESSING=1
mkdir -p $OUT_DIR
mkdir -p $BUILD_DIR

pushd $BUILD_DIR
# get the target line
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c ./file.c
ABORT_LINE=`awk '/abort*/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE > $AFLGO_TARGET_DIR/BBtargets.txt
# generate CFGs and call graph
$MAZERUNNER_SRC/build/bin/ko-clang -g -o ${PROGRAM_NAME}_preprocessing ./file.c
# compute distaces
$TOOL_DIR/static_analysis.py $AFLGO_TARGET_DIR
# compilation with distance instrumentation
unset AFLGO_PREPROCESSING
$MAZERUNNER_SRC/build/bin/ko-clang -g -O3 -o ${PROGRAM_NAME}_symsan_NM ./file.c
popd

# create coverage tracing directory
COV_DIR="${OUT_DIR}/maze_cov"
mkdir -p "$COV_DIR"
export MAZE_COV="${COV_DIR}/accumulated_counter"
python3 -c "print('0\n' * ${MAZE_SIZE})" > $MAZE_COV

ulimit -c 0
# Create dummy file to indicate running start
touch $WORKDIR/.start

# fuzz
nohup timeout $TIMEOUT python3 ${TOOL_DIR}/visualize_maze_cov.py ${MAZE_DIR}/txt/${MAZE_TXT}.txt ${COV_DIR}/accumulated_counter $MAZE_SIZE > ${OUT_DIR}/visualize.log 2>&1 &
nohup timeout $TIMEOUT > ${OUT_DIR}/mazerunner.log 2>&1 &