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
export LLVM_COMPILER=clang

sudo chown -R maze:maze $MAZE_DIR
# create initial seed directory
if [[ ! -d "$IN_DIR" ]] || [[ ! -f "${IN_DIR}/init" ]]; then
    mkdir -p $IN_DIR
    python3 -c "print('A' * 2048)" > ${IN_DIR}/init
fi

pushd $WORKDIR
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c ./file.c
ABORT_LINE=`awk '/abort*/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE > ./BBtargets.txt

# 2.3.1 Generate bitcode file
wllvm file.c -g -o file.bin
extract-bc file.bin
# 2.3.2 Static Analysis
$BEACON/precondInfer/build/bin/precondInfer ${WORKDIR}/file.bin.bc --target-file=${WORKDIR}/BBtargets.txt --join-bound=5
# 2.3.3 Instrumentation
$BEACON/Ins/build/Ins -output=${WORKDIR}/file.bin.bc -blocks=bbreaches.txt -afl -log=log.txt -load=range_res.txt ./transed.bc
# 2.3.4 Compilation
clang ${WORKDIR}/file.bin.bc -o ${WORKDIR}/file.bin_instrumented -lm -lz $BEACON/Fuzzer/afl-llvm-rt.o
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
nohup timeout $TIMEOUT $BEACON/Fuzzer/afl-fuzz -t 2000+ -m none -i $IN_DIR -o $OUT_DIR -- ${WORKDIR}/file.bin_instrumented > ${OUT_DIR}/beacon.log 2>&1 &
