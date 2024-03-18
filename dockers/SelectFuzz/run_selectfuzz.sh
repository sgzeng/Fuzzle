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
TTE="$((3*${3}/4))m"

# create initial seed directory
if [[ ! -d "$IN_DIR" ]] || [[ ! -f "${IN_DIR}/init" ]]; then
    mkdir -p $IN_DIR
    python3 -c "print('A' * 1024)" > ${IN_DIR}/init
fi

export SELECTFUZZ=/selectfuzz; export SUBJECT=${WORKDIR}/obj-aflgo; export TMP_DIR=${WORKDIR}/obj-aflgo/temp
mkdir -p ${WORKDIR}/obj-aflgo/temp

cd $SUBJECT
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c file.c
ABORT_LINE=`awk '/func_bug\(input/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE > $TMP_DIR/BBtargets.txt
ABORT_LINE=`awk '/abort*/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE >> $TMP_DIR/BBtargets.txt

# first build
$SELECTFUZZ/afl-clang-fast -targets=$TMP_DIR/BBtargets.txt -outdir=$TMP_DIR -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps -lpthread -o ${SUBJECT}/file.bin ${SUBJECT}/file.c

# clean up
cat $TMP_DIR/BBnames.txt | rev | cut -d: -f2- | rev | sort | uniq > $TMP_DIR/BBnames2.txt && mv $TMP_DIR/BBnames2.txt $TMP_DIR/BBnames.txt
cat $TMP_DIR/BBcalls.txt | sort | uniq > $TMP_DIR/BBcalls2.txt && mv $TMP_DIR/BBcalls2.txt $TMP_DIR/BBcalls.txt

# generate distances
$SELECTFUZZ/scripts/genDistance.sh $SUBJECT $TMP_DIR ${SUBJECT}/file.bin
# second build
$SELECTFUZZ/afl-clang-fast -g -distance=$TMP_DIR/distance.cfg.txt -lpthread -o ${SUBJECT}/file_run.bin ${SUBJECT}/file.c

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
nohup timeout $TIMEOUT $SELECTFUZZ/afl-fuzz -t 2000+ -m none -z exp -c $TTE -i $IN_DIR -o $OUT_DIR -- ${SUBJECT}/file_run.bin > ${OUT_DIR}/selectfuzz.log 2>&1 &

# Wait for the timeout and kill the container
sleep 1s
sleep $TIMEOUT && touch $WORKDIR/.done