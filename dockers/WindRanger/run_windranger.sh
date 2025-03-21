#!/bin/bash
set -e

export PATH=/home/maze/tools/windranger/clang+llvm/bin:$PATH
export PATH=/home/maze/tools/windranger/gllvm:$PATH

MAZE_DIR=$1
PROGRAM_NAME=$2
TIMEOUT="${3}m"
MAZE_SIZE=$4
MAZE_TXT=$5
WORKDIR=/home/maze/workspace
TOOL_DIR=/home/maze/tools
IN_DIR="${WORKDIR}/inputs"
OUT_DIR="${WORKDIR}/outputs"
TTE="$((3*${3}/4))m"

# create initial seed directory
if [[ ! -d "$IN_DIR" ]] || [[ ! -f "${IN_DIR}/init" ]]; then
    mkdir -p $IN_DIR
    python3 -c "print('A' * 1024)" > ${IN_DIR}/init
fi

cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c $WORKDIR/file.c

touch $WORKDIR/.sa_start

ABORT_LINE=`awk '/func_bug\(input/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE > $TMP_DIR/BBtargets.txt
ABORT_LINE=`awk '/abort*/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE >> $TMP_DIR/BBtargets.txt

export CC="gclang"
export CXX="gclang++"

$CC -o file file.c

get-bc file
/home/maze/tools/windranger/instrument/bin/cbi --targets=$TMP_DIR/BBtargets.txt ./file.bc
/home/maze/tools/windranger/fuzz/afl-clang-fast ./file.bc -o ./file.bin

# create coverage tracing directory
COV_DIR="${OUT_DIR}/maze_cov"
mkdir -p "$COV_DIR"
export MAZE_COV="${COV_DIR}/accumulated_counter"
python3 -c "print('0\n' * ${MAZE_SIZE})" > $MAZE_COV

ulimit -c 0
# Create dummy file to indicate running start
touch $WORKDIR/.start

# fuzz
nohup timeout $TIMEOUT python3 ${TOOL_DIR}/visualize_maze_cov.py ${MAZE_DIR}/txt/${MAZE_TXT}.txt ${COV_DIR}/accumulated_counter $MAZE_SIZE ${OUT_DIR}/crashes > ${OUT_DIR}/visualize.log 2>&1 &
nohup timeout $TIMEOUT $AFLGO/afl-2.57b/afl-fuzz -t 2000+ -m none -z exp -c $TTE -i $IN_DIR -o $OUT_DIR -- ./file_run.bin > ${OUT_DIR}/aflgo.log 2>&1 &

# Wait for the timeout and kill the container
sleep 1s
sleep $TIMEOUT && touch $WORKDIR/.done