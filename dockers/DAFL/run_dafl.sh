#!/bin/bash
set -e

MAZE_DIR=$1
PROGRAM_NAME=$2
TIMEOUT="${3}m"
MAZE_SIZE=$4
MAZE_TXT=$5
WORKDIR=/home/maze/workspace
TOOL_DIR=/home/maze/tools
SEED_DIR="${WORKDIR}/seed"
OUT_DIR="${WORKDIR}/outputs"
INDIR=$WORKDIR/dafl-input

# create initial seed directory
if [[ ! -d "$SEED_DIR" ]] || [[ ! -f "${SEED_DIR}/init" ]]; then
    mkdir -p $SEED_DIR
    python3 -c "print('A' * 1024)" > ${SEED_DIR}/init
fi
mkdir $OUT_DIR

rm -rf $WORKDIR/src/*
rm -rf $INDIR/*

# copy makefile
cp /home/maze/script/clang-compile.mk $WORKDIR/src/Makefile
cp /home/maze/script/dafl-compile-noasan.mk $INDIR/Makefile

# target source code copy
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c $WORKDIR/src/file.c
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c $INDIR/file.c

# run smake
cd $WORKDIR/src
yes | /home/maze/smake/smake --init
/home/maze/smake/smake -j 1
cp sparrow/file/00.file.c.i ./

# target line set
TARGET_LINE=$(awk '/\tfunc_bug*/ { print NR }' file.c)
TARGET="file.c:$TARGET_LINE"

# run sparrow
mkdir -p $WORKDIR/src/sparrow-output
/home/maze/sparrow/bin/sparrow -outdir $WORKDIR/src/sparrow-output -frontend cil -unsound_alloc -unsound_const_string \
-unsound_recursion -unsound_noreturn_function -unsound_skip_global_array_init 1000 -skip_main_analysis -cut_cyclic_call \
-unwrap_alloc -entry_point main -max_pre_iter 100 -slice target="$TARGET" $WORKDIR/src/00.file.c.i

# DAFL Compile
cp $WORKDIR/src/sparrow-output/target/slice_func.txt $INDIR/target_selective_cov
cp $WORKDIR/src/sparrow-output/target/slice_dfg.txt $INDIR/target_dfg
export DAFL_SELECTIVE_COV="$INDIR/target_selective_cov"
export DAFL_DFG_SCORE="$INDIR/target_dfg"
cd $INDIR && make &> $OUT_DIR/build.log

# Fuzzing setting
unset ASAN_OPTIONS
export AFL_NO_AFFINITY=1
export AFL_SKIP_CRASHES=1
export UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1

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
nohup timeout $TIMEOUT /home/maze/fuzzer/DAFL/afl-fuzz -t 2000+ -m none -d -i $SEED_DIR -o $OUT_DIR -- /home/maze/workspace/dafl-input/file_dafl  > ${OUT_DIR}/dafl.log 2>&1 &

# Wait for the timeout and kill the container
sleep 1s
sleep $TIMEOUT && touch $WORKDIR/.done