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

# create initial seed directory
if [[ ! -d "$IN_DIR" ]] || [[ ! -f "${IN_DIR}/init" ]]; then
    mkdir -p $IN_DIR
    python3 -c "print('A' * 2048)" > ${IN_DIR}/init
fi

pushd $WORKDIR
cp ${MAZE_DIR}/src/${PROGRAM_NAME}.c ./file.c
ABORT_LINE=`awk '/func_bug\(input/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE > $TMP_DIR/BBtargets.txt
ABORT_LINE=`awk '/abort*/ { print NR }' file.c`
echo 'file.c:'$ABORT_LINE >> $TMP_DIR/BBtargets.txt

# 2.3.1 Generate bitcode file
$CLANGDIR/clang -g -c -emit-llvm file.c -o file.bc
# 2.3.2 Static Analysis
$BEACON/precondInfer file.bc --target-file=BBtargets.txt --join-bound=5 > precond_log 2>&1
# 2.3.3 Instrumentation
$BEACON/Ins -output=beacon_file.bc -byte -blocks=bbreaches_BBtargets.txt -afl -log=log.txt -load=range_res.txt transed.bc
# 2.3.4 Compilation
$CLANGDIR/clang -rdynamic beacon_file.bc -o file.bin_instrumented -lm -lz -ldl $BEACON/afl-llvm-rt.o

# create coverage tracing directory
COV_DIR="${OUT_DIR}/maze_cov"
mkdir -p "$COV_DIR"
export MAZE_COV="${COV_DIR}/accumulated_counter"
python3 -c "print('0\n' * ${MAZE_SIZE})" > $MAZE_COV

# create the exit wrapper for LD_PRELOAD
EXIT_WRAPPER="exit_wrapper.c"
cat <<EOF > "$EXIT_WRAPPER"
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <unistd.h>

// Global variables to hold the pointers to the original functions
void (*original_exit)(int status) = NULL;
void (*original__exit)(int status) = NULL;

__attribute__((constructor))
void init(void) {
    original_exit = (void (*)(int))dlsym(RTLD_NEXT, "exit");
    original__exit = (void (*)(int))dlsym(RTLD_NEXT, "_exit");
}

void exit(int status) {
    unsigned int* counter = (unsigned int*)dlsym(RTLD_DEFAULT, "counter");
    if (counter) {
        const char* filepath = getenv("MAZE_COV");
        if (filepath == NULL) {
            printf("output_counter: print to screen");
            for (int i = 0; i < ${MAZE_SIZE}; i++) {
                if (counter[i] != 0) {
                    printf("counter[%d] = %u\n", i, counter[i]);
                }
            }
        }
        else {
            FILE* file = fopen(filepath, "w");
            printf("output_counter: write to file");
            if (file != NULL) {
                for (int i = 0; i < ${MAZE_SIZE}; i++) {
                    fprintf(file, "%u\n", counter[i]);
                }
                fclose(file);
            }
        }
    }
    if (original_exit) {
        original_exit(status);
    }

    // If dlsym failed, this will still be an infinite loop, but we should never get here.
    while (1) {}
}
EOF
$CLANGDIR/clang -fPIC -shared -o exit_wrapper.so exit_wrapper.c -ldl
# create the bin_instrumented wrapper for ENV variables
BIN_WRAPPER="file.bin_instrumented_wrapper.c"
cat <<EOF > "$BIN_WRAPPER"
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    setenv("LD_PRELOAD", "${WORKDIR}/exit_wrapper.so", 1);
    setenv("MAZE_COV","${MAZE_COV}", 1);
    execv("${WORKDIR}/file.bin_instrumented", argv);
    return 0;
}
EOF
$CLANGDIR/clang -o file.bin_instrumented_wrapper file.bin_instrumented_wrapper.c -ldl $BEACON/afl-llvm-rt.o

popd

ulimit -c 0
# Create dummy file to indicate running start
touch $WORKDIR/.start

# fuzz
nohup timeout $TIMEOUT python3 ${TOOL_DIR}/visualize_maze_cov.py ${MAZE_DIR}/txt/${MAZE_TXT}.txt ${COV_DIR}/accumulated_counter $MAZE_SIZE > ${OUT_DIR}/visualize.log 2>&1 &
nohup timeout $TIMEOUT $BEACON/afl-fuzz -t 2000+ -m none -i $IN_DIR -o $OUT_DIR -d -- ${WORKDIR}/file.bin_instrumented_wrapper > ${OUT_DIR}/beacon.log 2>&1 &
