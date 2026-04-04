# Fuzzle

Fuzzle synthesizes buggy C programs for evaluating directed grey-box fuzzers.
It wraps randomly generated mazes (optionally seeded with real CVE path constraints) in compilable C source, then drives any supported fuzzer inside an isolated Docker container.

---

## Repository Layout

```
Fuzzle/
  maze-gen/      Python maze + C-code generators
  CVEs/          *.smt2 constraint files (6 CVEs: CVE-2016-{4487,4489,4491,4492,4493,6131})
  scripts/       generate.sh  generate_benchmark.py  run_tools.py
                 save_results.sh  visualize.py
  dockers/       One subdir per tool: Dockerfile + run_*.sh
  examples/      example{1,2,3}.{list,conf}  (ready-to-run sets)
  tutorial/      programs.list + run.conf    (quick 5-min smoke test)
```

A generated benchmark directory contains:

```
<OUT>/
  src/   *.c                   C source (gcc -O0 -g)
  bin/   *.bin                 compiled binaries
  txt/   *.txt                 maze array (used by visualizer)
  png/   *.png                 maze image
  sln/   *_solution.txt        shortest solution path
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.7+ | host-side generation only |
| gcc | compiles generated C during `generate.sh` |
| Z3 solver | required for CVE-based generation |
| Docker | superuser access; images must be pre-built |

```bash
pip install -r maze-gen/requirements.txt
pysmt-install --z3        # install Z3 for pySMT
pysmt-install --check     # verify
```

---

## Generating Maze Programs

### Single program

```bash
./scripts/generate.sh -a Wilsons -w 10 -h 10 -o /out/path

# Key flags:
#   -a  algorithm   Backtracking | Kruskal | Prims | Wilsons | Sidewinder
#   -w  width       integer > 2
#   -h  height      integer > 2
#   -o  output dir
#   -r  seed        default 1
#   -n  count       number of mazes to generate, default 1
#   -c  cycles%     0–100, default 100
#   -e  exit        default | random
#   -g  generator   default_gen | CVE_gen  (CVE_gen requires -s)
#   -s  smt2 path   e.g. CVEs/CVE-2016-4487.smt2
```

CVE-based example:

```bash
./scripts/generate.sh -a Wilsons -w 10 -h 10 \
    -g CVE_gen -s CVEs/CVE-2016-4487.smt2 -o /out/path
```

### Batch generation

Create a `programs.list` file — one program per line:

```
<algorithm>,<width>,<height>,<seed>,<index>,<N>percent,<generator>
```

`generator` is either `default_gen` or `CVE-2016-4487_gen` (the CVE prefix is resolved automatically to the matching `.smt2` file in `CVEs/`).

Example:

```
Wilsons,10,10,1,1,100percent,default_gen
Wilsons,10,10,1,1,100percent,CVE-2016-4487_gen
Backtracking,30,30,1,1,25percent,default_gen
```

Run:

```bash
python3 scripts/generate_benchmark.py programs.list /out/path
```

---

## Docker Images

`run_tools.py` selects images by the rule `image = "maze-" + tool_name` (with `afl++` → `aflpp`).

| `Tools` value in `.conf` | Docker image |
|---|---|
| `afl++` | `maze-aflpp` |
| `aflgo` | `maze-aflgo` |
| `beacon-prebuilt` | `maze-beacon-prebuilt` |
| `beacon-src` | `maze-beacon-src` |
| `selectfuzz` | `maze-selectfuzz` |
| `dafl` | `maze-dafl` |
| `mazerunner-exploit-max` | `maze-mazerunner-exploit-max` |
| `mazerunner-exploit-avg` | `maze-mazerunner-exploit-avg` |
| `mazerunner-explore-max` | `maze-mazerunner-explore-max` |
| `mazerunner-explore-avg` | `maze-mazerunner-explore-avg` |
| `mazerunner-wo-policy` | `maze-mazerunner-wo-policy` |
| `mazerunner-norl-avg` | `maze-mazerunner-norl-avg` |
| `mazerunner-aflgo-solver` | `maze-mazerunner-aflgo-solver` |
| `mazerunner-single-state` | `maze-mazerunner-single-state` |

> **`maze-afl`** (classic AFL) is commented out in `build_all_dockers.sh` and not built by default — use `afl++` instead.
>
> **`maze-windranger`** is pre-built but `windranger` is absent from `run_tools.py`'s `TOOLS` list; manual integration required.

### Container filesystem contract

`run_tools.py` does the following per experiment:

1. `docker run maze-<tool>` — spawns a fresh container, pinned to 2 CPUs, 4 GB RAM.
2. `docker cp <MazeDir> <container>:/home/maze/maze` — injects the benchmark.
3. Executes inside the container: `/home/maze/tools/run_<tool>.sh <maze_dir> <bin_name> <duration_min> <maze_size> <maze_txt_base>`.
4. On completion: copies `/home/maze/outputs` and `/home/maze/workspace/outputs` out to the host, then removes the container.

The script names inside each image must match exactly: `run_aflgo.sh`, `run_dafl.sh`, `run_mazerunner-exploit-max.sh`, etc.

### Tuning resource constants

Edit the top of `scripts/run_tools.py` before running:

```python
NUM_WORKERS    = 15   # max parallel containers
LOGICAL_CPU_NUM = 32  # logical cores on your machine
# SPAWN_CMD uses -m=4g; change the docker run template if needed
```

---

## Running a Fuzzing Experiment

### 1. Write a config file

```json
{
    "MazeList" : "/abs/path/programs.list",
    "Repeats"  : 1,
    "Duration" : 60,
    "MazeDir"  : "/abs/path/benchmark",
    "Tools"    : ["afl++", "aflgo", "mazerunner-exploit-max"]
}
```

- `MazeList` — same format as used during generation.
- `Duration` — in minutes.
- Paths may be absolute or relative to `scripts/`.

### 2. Launch

```bash
cd scripts
python3 run_tools.py my.conf /abs/path/outputs
```

### Output structure

```
outputs/
  <algo>_<W>x<H>_<seed>_<idx>_<cycle>_<gen>/
    <tool>-<epoch>/
      outputs/          raw fuzzer queue & crashes
      outputs/.done     sentinel file — written when campaign ends
      result/           workspace outputs (mazerunner variants only)
      cov_txt_*/        line-level coverage text
      cov_gcov_*/       gcov directory (used by save_results & visualize)
```

---

## Static Analysis

Each `run_<tool>.sh` performs its own pre-fuzzing static analysis automatically — no host-side step is required.

| Tool | Static analysis step |
|---|---|
| AFLGo, SelectFuzz | LTO compile → compute CFG distances (`afl-clang-fast -distance=...`) |
| Beacon-prebuilt | `precondInfer file.bc` (LLVM 4 + SVF, precondition inference) |
| Beacon-src | `wllvm` bitcode extraction → `precondInfer/build/bin/precondInfer` |
| MazeRunner | `clang-12` preprocessing binary → `static_analysis.py` (distance from `BBtargets.txt`) |
| DAFL | Sparrow analyzer → `afl-clang-fast` instrumentation |

The target line in each generated program is always the call to `func_bug(input, ...)`, which all toolchains identify automatically with `awk '/func_bug\(input/ { print NR }'`.

### Custom host-side analysis

The generated C source files are self-contained and can be compiled with any toolchain:

```bash
# Emit LLVM bitcode for custom analysis:
clang -emit-llvm -g -c \
    benchmark/src/Wilsons_10x10_1_1_100percent_default_gen.c -o out.bc

# Or run Clang Static Analyzer:
scan-build gcc -O0 -g benchmark/src/*.c
```

---

## Collecting Results

### Summarize

```bash
./scripts/save_results.sh <FUZZ_OUT> <RESULT_CSV> <PARAM> <DURATION_h> <MODE>
```

| Argument | Values |
|---|---|
| `PARAM` | `Algorithm` \| `Size` \| `Cycle` \| `Generator` |
| `DURATION_h` | hours elapsed (use `0` for full run) |
| `MODE` | `paper` (per-algorithm table) \| `fuzzer` (per-fuzzer summary) |

Example:

```bash
./scripts/save_results.sh outputs/ results.csv Algorithm 24 paper
```

### Visualize coverage on maze grid

```bash
python3 scripts/visualize.py \
    benchmark/txt/Wilsons_10x10_1_1.txt \
    outputs/<maze>/<tool>-0/cov_gcov_*/Wilsons_*.c.gcov \
    out/wilsons \
    10        # maze width (= height for square mazes)
```

Produces `out/wilsons.png`: each cell represents one function; green = covered, red = not covered.

---

## End-to-End Example (tutorial)

```bash
# 1. Generate 5 programs (20x20, 5 algorithms, default_gen)
cd scripts
python3 generate_benchmark.py ../tutorial/programs.list ../tutorial/benchmark

# 2. Fuzz with AFL for 5 minutes each
python3 run_tools.py ../tutorial/run.conf ../tutorial/outputs

# 3. Summarize and visualize
./save_results.sh ../tutorial/outputs ../tutorial/results Algorithm 0 paper \
    > ../tutorial/summary
cat ../tutorial/summary

python3 visualize.py \
    ../tutorial/benchmark/txt/Wilsons_20x20_1_1.txt \
    ../tutorial/outputs/Wilsons_20x20_1_1_25percent_default_gen/afl-0/cov_gcov_*/Wilsons_*.c.gcov \
    ../tutorial/wilsons 20
```

---

## Citation

```bibtex
@INPROCEEDINGS{lee:ase:2022,
  author    = {Haeun Lee and Soomin Kim and Sang Kil Cha},
  title     = {{Fuzzle}: Making a Puzzle for Fuzzers},
  booktitle = {Proceedings of the International Conference on Automated Software Engineering},
  year      = 2022
}
```
