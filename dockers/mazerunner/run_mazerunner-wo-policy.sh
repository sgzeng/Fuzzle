#!/bin/bash
set -euo pipefail

eval "$(pyenv init -)"

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
    python3 -c "print('A' * 1024)" > ${IN_DIR}/init
fi

export BUILD_DIR=$WORKDIR/build
export MAZERUNNER_SRC=/workdir/symsan
export KO_CXX=clang++-12
export KO_CC=clang-12
export CXX=$MAZERUNNER_SRC/build/bin/ko-clang++
export CC=$MAZERUNNER_SRC/build/bin/ko-clang
export KO_USE_FASTGEN=1
export KO_ADD_AFLGO=1
export KO_DONT_OPTIMIZE=1
export AFLGO_TARGET_DIR=$BUILD_DIR/targets
export AFLGO_PREPROCESSING=1
mkdir -p $OUT_DIR
mkdir -p $AFLGO_TARGET_DIR

pushd $BUILD_DIR
# get the target line
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c ./file.c
ABORT_LINE=`awk '/func_bug\(input/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE > $AFLGO_TARGET_DIR/BBtargets.txt
# generate CFGs and call graph
$CC -g -o ${PROGRAM_NAME}_preprocessing ./file.c
# compute distaces
python3 $MAZERUNNER_SRC/mazerunner/static_analysis.py $AFLGO_TARGET_DIR
rm ${AFLGO_TARGET_DIR}/policy.pkl
# compilation with distance instrumentation
unset AFLGO_PREPROCESSING
$CC -g -o ${PROGRAM_NAME}_symsan_NM ./file.c
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
nohup timeout $TIMEOUT python3 ${TOOL_DIR}/visualize_maze_cov.py ${MAZE_DIR}/txt/${MAZE_TXT}.txt ${COV_DIR}/accumulated_counter $MAZE_SIZE ${OUT_DIR}/mazerunner/crashes > ${OUT_DIR}/visualize.log 2>&1 &
cd $MAZERUNNER_SRC && nohup timeout $TIMEOUT python3 mazerunner/mazerunner.py -a explore -i $IN_DIR -m reachability -o $OUT_DIR -s $AFLGO_TARGET_DIR -- $BUILD_DIR/${PROGRAM_NAME}_symsan_NM > ${OUT_DIR}/mazerunner.log 2>&1 &

# Wait for the timeout and kill the container
sleep 1s
sleep $TIMEOUT && touch $WORKDIR/.done