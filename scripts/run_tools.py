import os
import sys
import json
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# FIX accordingly (num maximum cores)
NUM_WORKERS = 15

TOOLS = ['afl', 'afl++', 'aflgo', 'eclipser', 'fuzzolic', 'beacon-prebuilt', 'beacon-src', 'selectfuzz', 'dafl', 'mazerunner-w-policy', 'mazerunner-wo-policy']

# FIX accordingly (memory limit)
LOGICAL_CPU_NUM = 32
SPAWN_CMD = 'docker run -m=4g --cpuset-cpus=%d,%d -it -d --name %s %s'
START_CMD = 'docker start %s'
RM_CMD = 'docker rm %s'
WAIT_CMD = 'docker wait %s'
TEST_CMD = "docker exec %s sh -c '[ -f %s ] && echo YES || echo NO'"
CP_MAZE_CMD = 'docker cp %s %s:/home/maze/maze'
CP_RESULT_CMD = 'docker cp %s:/home/maze/workspace/outputs %s'
CP_CMD = 'docker cp %s:/home/maze/outputs %s'
COMPILE_CMD = 'gcc -fprofile-arcs -ftest-coverage -o %s %s -lgcov --coverage'
REPLAY_CMD = 'cat %s | ./%s'
GCOV_CMD = 'gcov -b -c -s %s %s > %s'
CP_FRCON_CMD = 'docker cp %s:%s %s'
MOVE_CMD = 'mv %s %s'
REMOVE_CMD = 'rm %s %s %s %s'
KILL_CMD = 'docker kill %s'
CHOWN_CMD = 'sudo chown -R maze:maze %s'

def run_cmd(cmd_str):
    print("[*] Executing: %s" % cmd_str)
    cmd_args = cmd_str.split()
    try:
        subprocess.call(cmd_args)
    except Exception as e:
        print(e)
        exit(1)

def run_cmd_in_docker(container, cmd_str):
    print("[*] Executing (in container): %s" % cmd_str)
    cmd_prefix = "docker exec -d %s /bin/bash -c" %  container
    cmd_args = cmd_prefix.split()
    cmd_args += [cmd_str]
    try:
        subprocess.call(cmd_args)
    except Exception as e:
        print(e)
        exit(1)

def file_exists_in_container(container, file_path):
    command = TEST_CMD % (container, file_path)
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "YES" in result.stdout:
        return True
    else:
        return False
            
def load_config(path):
    with open(path) as f:
        txt = f.read()
    conf = json.loads(txt)

    assert os.path.exists(conf['MazeList']) and os.path.isfile(conf['MazeList'])
    assert conf['Repeats'] > 0
    assert conf['Duration'] > 0
    assert os.path.exists(conf['MazeDir']) and os.path.isdir(conf['MazeDir'])
    for tool in conf['Tools']:
        assert tool in TOOLS

    return conf

def get_targets(conf):
    targets = []

    with open(conf['MazeList']) as f:
        for line in f.readlines():
            tokens = line.strip().split(',')
            algo, width, height, seed, num, cycle, gen = tokens[0], tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], tokens[6]
            for tool in conf['Tools']:
                for epoch in range(conf['Repeats']):
                    target = algo, width, height, seed, num, cycle, gen, tool, epoch
                    targets.append(target)

    return targets

def start_container(conf, task, i):
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    image = 'maze-%s' % tool_
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    # Spawn a container
    cmd = SPAWN_CMD % (i, i+LOGICAL_CPU_NUM/2, container, image)
    run_cmd(cmd)
    # Copy maze in the container
    cmd = CP_MAZE_CMD % (conf['MazeDir'], container)
    run_cmd(cmd)
    cmd = CHOWN_CMD % '/home/maze/maze'
    run_cmd_in_docker(container, cmd)
    
def resume_container(conf, task):
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    image = 'maze-%s' % tool_
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    cmd = START_CMD % container
    run_cmd(cmd)

def get_maze_name(algo, width, height, seed, num, cycle, gen):
    return '%s_%sx%s_%s_%s' % (algo, width, height, seed, num)

def get_put_name(algo, width, height, seed, num, cycle, gen):
    return '%s_%sx%s_%s_%s_%s_%s' % (algo, width, height, seed, num, cycle, gen)

def get_src_path(algo, width, height, seed, num, cycle, gen, tool):
    bin_name = get_put_name(algo, width, height, seed, num, cycle, gen)
    if tool == 'klee':
        src_path = f'/home/maze/maze/src/{bin_name}_klee.c'
    else:
        src_path = f'/home/maze/maze/src/{bin_name}.c'
    return src_path

def get_bin_path(algo, width, height, seed, num, cycle, gen):
    bin_name = get_put_name(algo, width, height, seed, num, cycle, gen)
    return f'/home/maze/maze/bin/{bin_name}.bin'

def get_container_name(task):
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    return container

def run_tool(conf, task):
    duration = int(conf['Duration'])
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    script = '/home/maze/tools/run_%s.sh' % tool
    bin_name = get_put_name(algo, width, height, seed, num, cycle, gen)
    maze_txt_name = get_maze_name(algo, width, height, seed, num, cycle, gen)
    maze_dir = '/home/maze/maze'
    maze_size = str(int(width) * int(height))
    cmd = f'{script} {maze_dir} {bin_name} {duration} {maze_size} {maze_txt_name}'
    run_cmd_in_docker(container, cmd)
    while not file_exists_in_container(container, '/home/maze/workspace/.done'):
        time.sleep(60)
    kill_container(task)

def store_outputs(conf, out_dir, task):
    duration = int(conf['Duration'])
    # First, collect testcases in /home/maze/outputs
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    cmd = 'python3 /home/maze/tools/get_tcs.py /home/maze/outputs'
    run_cmd_in_docker(container, cmd)

    time.sleep(duration)

    # Next, store outputs to host filesystem
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    maze = get_put_name(algo, width, height, seed, num, cycle, gen)
    # copy the tc directory
    out_path = os.path.join(out_dir, maze, '%s-%d' % (tool, epoch))
    os.system('mkdir -p %s' % out_path)
    cmd = CP_CMD % (container, out_path)
    run_cmd(cmd)
    # copy the result directory
    out_path = os.path.join(out_dir, maze, '%s-%d' % (tool, epoch), 'result')
    cmd = CP_RESULT_CMD % (container, out_path)
    run_cmd(cmd)
    time.sleep(duration)

def store_coverage(conf, out_dir, task):
    duration = int(conf['Duration'])
    # Measure coverage and save results
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    maze = '%s_%sx%s_%s_%s_%s_%s' % (algo, width, height, seed, num, cycle, gen)
    maze_tool = maze + '_%s_%d' % (tool_, epoch)
    if tool == 'klee':
        is_klee = '_klee'
    else:
        is_klee = ''
    script = '/home/maze/tools/get_coverage.sh'
    tc_dir = '/home/maze/outputs'
    src_dir = '/home/maze/maze/src'
    src_name = maze + is_klee
    cmd = '%s %s %s %s %s %s' % (script, tc_dir, src_dir, src_name, maze_tool, duration)
    run_cmd_in_docker(container, cmd)

    time.sleep(duration * 2)

    # Store coverage results to host filesystem
    algo, width, height, seed, num, cycle, gen, tool, epoch = task
    if tool == 'afl++':
        tool_ = 'aflpp'
    else:
        tool_ = tool
    container = '%s-%sx%s-%s-%s-%s-%s-%s-%d' % (algo, width, height, seed, num, cycle, gen, tool_, epoch)
    maze = get_put_name(algo, width, height, seed, num, cycle, gen)
    maze_tool = maze + '_%s_%d' % (tool_, epoch)
    out_path = os.path.join(out_dir, maze)
    cmd = CP_FRCON_CMD % (container, '/home/maze/outputs/cov_txt_' + maze_tool, out_path)
    run_cmd(cmd)
    cmd = CP_FRCON_CMD % (container, '/home/maze/outputs/cov_gcov_' + maze_tool, out_path)
    run_cmd(cmd)

    time.sleep(duration)

def kill_container(task):
    container = get_container_name(task)
    cmd = KILL_CMD % container
    run_cmd(cmd)

def remove_container(task):
    container = get_container_name(task)
    cmd = RM_CMD % container
    run_cmd(cmd)    

def run_experiment(task, cpu_id):
    start_container(conf, task, cpu_id)
    run_tool(conf, task)
    resume_container(conf, task)
    store_outputs(conf, out_dir, task)
    store_coverage(conf, out_dir, task)
    kill_container(task)
    remove_container(task)
    
def main(conf_path, out_dir):
    os.system('mkdir -p %s' % out_dir)
    targets = get_targets(conf)
    print(targets)
    cpus = [i for i in range(NUM_WORKERS)]
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(run_experiment, t, cpus[i % len(cpus)]) for i, t in enumerate(targets)]
        for future in as_completed(futures):
            future.result()

if __name__ == '__main__':
    global conf, out_dir
    conf_path = sys.argv[1]
    out_dir = sys.argv[2]
    conf = load_config(conf_path)
    main(conf_path, out_dir)
