import json
import os
import sys
import csv
import subprocess
from collections import defaultdict
from glob import glob

TOOLS = ['afl', 'afl++', 'aflgo', 'eclipser', 'fuzzolic', 'beacon-prebuilt', 'beacon-src', 'selectfuzz', 'dafl', 'mazerunner-w-policy', 'mazerunner-wo-policy']

def get_coverage_files(output_dir):
    coverage_files = []
    for filename in glob(output_dir + '/**/cov_txt*/*txt', recursive=True):
        coverage_files.append(filename)
    return coverage_files

def write_row_headers(writer):
    headers = ["Algorithm", "Size", "Seed", "Cycle Proportion",
     "Generator", "Tool", "Epoch",
     "Lines executed", "Branches executed", "Taken at least once",
     "Calls executed", "Time taken to first crash"]
    writer.writerow(headers)

def write_rows(writer, filenames, time):
    def sort_helper(fp):
        basename = os.path.basename(fp)
        file_number = os.path.splitext(basename)[0]
        if 'error' in file_number:
            return -1
        return -int(file_number)
    
    def get_target_visited_times(cov_file, msize):
        visited_fun_count = 0
        with open(cov_file) as f:
            lines = f.readlines()
            if len(lines) == msize + 1:
                visited_fun_count = int(lines[-2].strip())
            elif len(lines) == msize:
                visited_fun_count = int(lines[-1].strip())
        return visited_fun_count
    
    for summary_txt in filenames:
        if not '{}h'.format(time) in summary_txt:
            continue
        maze = summary_txt.split('/')[-1].strip('.txt\n').split('_')
        tool =maze[7]
        if tool == 'aflpp':
            tool_ = 'afl++'
        else:
            tool_ = tool
        tool_dir = f'{tool_}-{maze[8]}'
        exp_dir = os.path.dirname(os.path.dirname(summary_txt))
        seeds_dir = os.path.join(exp_dir, tool_dir, 'outputs')
        msize = int(maze[1].split('x')[0])
        msize = msize * msize
        has_neg_ts = search_neg_ts(seeds_dir)
        with open(summary_txt) as f:
            row = []
            numb = 0
            for line in f:
                if numb == 0:
                    for idx in range(len(maze)):
                        if idx < 2:
                            row.append(maze[idx])
                        elif idx == 2 or idx == 8:
                            row.append(int(maze[idx]))
                        elif idx == 4:
                            row.append(int(maze[idx].strip('percent')))
                        elif idx == 5 or idx == 7:
                            row.append(maze[idx])
                        # elif idx == 9:
                        #     row.append(int(maze[idx].strip('hr')))
                    if len(maze) < 10:
                        row.append(0)
                if numb > 0 and numb < 5:
                    try:
                        coverage = line.split(':')[1].split('%')[0]
                    except:
                        coverage = 0
                    row.append(float(coverage))
                if '/home/maze/outputs/' in line and '_crash_abort' in line and not has_neg_ts:
                    time_taken = line.strip('/home/maze/outputs/').split('_')[0]
                    row.append(float(time_taken))
                    break
                numb = numb + 1
            if len(row) < 12:
                # try to get the time taken to first crash from the maze cov
                maze_cov_dir = os.path.join(exp_dir, tool_dir, 'result', 'maze_cov')
                maze_cov_files = glob(f'{maze_cov_dir}/*.txt')
                sorted_maze_cov_files = sorted(maze_cov_files, key=sort_helper)
                last_cov_file = os.path.join(maze_cov_dir, 'accumulated_counter')
                if os.path.getsize(last_cov_file) == 0 and maze_cov_files:
                    for cov_file in sorted_maze_cov_files:
                        if os.path.getsize(cov_file) > 0:
                            last_cov_file = cov_file
                            # print(f'using {last_cov_file}')
                            break
                assert os.path.getsize(last_cov_file) > 0, f'file {last_cov_file} is empty'
                targer_count = get_target_visited_times(last_cov_file, msize)
                if tool == 'aflpp':
                    crash_dir = os.path.join(exp_dir, tool_dir, 'result', 'default', 'crashes')
                    queue_dir = os.path.join(exp_dir, tool_dir, 'result', 'default', 'queue')
                elif 'mazerunner' in tool:
                    crash_dir = os.path.join(exp_dir, tool_dir, 'result', 'mazerunner', 'crashes')
                    queue_dir = os.path.join(exp_dir, tool_dir, 'result', 'mazerunner', 'queue')
                else:
                    crash_dir = os.path.join(exp_dir, tool_dir, 'result', 'crashes')
                    queue_dir = os.path.join(exp_dir, tool_dir, 'result', 'queue')
                crash_tcs = set()
                for tc in os.listdir(crash_dir):
                    if 'id' in tc:
                        crash_tcs.add(tc)
                if targer_count > 0 or crash_tcs:
                    bin_path = os.path.join(benchmark_dir, 'bin', f'{os.path.basename(exp_dir)}.bin')
                    crash_file = search_crash(seeds_dir, bin_path)
                    if crash_file is not None:
                        tte = float(crash_file.split('_')[0])
                        if has_neg_ts and tte < 0:
                            start_time = get_start_time(queue_dir)
                            tte = get_tte_from_crash_dir(crash_dir, start_time)
                            if tte == float('inf'):
                                tte = get_tte_from_queue_dir(queue_dir, start_time, bin_path)
                            assert tte > 0 and tte != float('inf'), f'tte is {tte}'
                        row.append(tte)
                    elif 'beacon' in tool:
                        for cov_file in reversed(sorted_maze_cov_files):
                            target_visited_times = get_target_visited_times(cov_file, msize)
                            if target_visited_times > 0:
                                tte = float(os.path.splitext(os.path.basename(cov_file))[0])
                                row.append(tte)
                                break
        writer.writerow(row)

def search_neg_ts(queue_dir):
    for tc in os.listdir(queue_dir):
        if '_tc' not in tc:
            continue
        ts = float(tc.split('_')[0])
        if ts < 0: 
            return True
    return False

def get_tte_from_crash_dir(crash_dir, start_time):
    tte = float('inf')
    tcs = os.listdir(crash_dir)
    if 'README.txt' in tcs:
        tcs.remove('README.txt')
    if not tcs:
        return tte
    for tc in tcs:
        if 'id:' not in tc:
            continue
        if 'ts:' in tc:
            tte = min(tte, float(tc.split('ts:')[1].split(',')[0])/1000)
        elif 'time:' in tc:
            tte = min(tte, float(tc.split('time:')[1].split(',')[0])/1000)
        else:
            ts = os.path.getmtime(os.path.join(crash_dir, tc)) - start_time
            tte = min(tte, ts)
    return tte    

def get_tte_from_queue_dir(queue_dir, start_time, bin_path):
    tc = search_crash(queue_dir, bin_path)
    assert tc is not None, f'no crash found in {queue_dir}'
    return start_time - os.path.getmtime(os.path.join(queue_dir, tc))

def get_start_time(queue_dir):
    times = []
    for tc in os.listdir(queue_dir):
        if 'id:' in tc:
            full_path = os.path.join(queue_dir, tc)
            times.append(os.path.getmtime(full_path))
    if times:
        earliest_time = min(times)
        return earliest_time
    else:
        return None

def search_crash(queue_dir, bin_path):
    # print(f'searching for crash in {queue_dir}')
    def sort_helper(fn):
        if '_crash' in fn:
            return float(fn.split('_')[0])
        if 'id:' not in fn or '_tc' not in fn:
            return -1
        return float(fn.split('_')[0]) * 1000

    sorted_tcs = sorted(os.listdir(queue_dir), key=sort_helper)
    for tc in sorted_tcs:
        if '_crash' in tc:
            return tc
        if 'id:' not in tc or '_tc' not in tc:
            continue
        fp = os.path.join(queue_dir, tc)
        with open(fp, 'rb') as testcase:
            try:
                result = subprocess.run([bin_path], stdin=testcase, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                if result.returncode != 0:
                    # print(f"Crash found in file: {tc}")
                    return tc
            except subprocess.TimeoutExpired:
                print(f"Execution timed out for file: {tc}")
            except Exception as e:
                print(f"Error executing file {tc}: {e}")
    return None

# group by parameter
def group_param(data, param):
    grouped = defaultdict(list)
    if param == "Algorithm":
        for row in data:
            grouped[row['Algorithm']].append(row)
    elif param == "Size":
        for row in data:
            grouped[row['Size']].append(row)
    elif param == "Cycle":
        for row in data:
                grouped[row['Cycle Proportion']].append(row)
    elif param == "Generator":
        for row in data:
                grouped[row['Generator']].append(row)
    else:
        print("Unsupported parameter")
        exit(1)
    return grouped

# get average branch coverage
def get_coverage(data):
    coverage_sum = 0.0
    for row in data:
        coverage_sum += float(row['Taken at least once'])
    average_cov = coverage_sum / len(data)
    return '%02.2f' % average_cov

# get bug finding success rate
def get_rate(data):
    total_bugs = 0
    for row in data:
        if row['Time taken to first crash'] != None and row['Time taken to first crash'] != '':
            total_bugs += 1
    average_percent = (total_bugs / len(data))*100
    return '%01.0f' % average_percent

# get average TTE
def get_TTE(data):
    TTE_sum = 0.0
    bug_count = 0
    for row in data:
        if row['Time taken to first crash'] != None and row['Time taken to first crash'] != '':
            TTE_sum += float(row['Time taken to first crash'])
            bug_count += 1
    if bug_count == 0:
        return '-'
    else:
        average_TTE = (TTE_sum / bug_count)/60
        return '%02.2f' % average_TTE

def print_results_fuzzer(data, tool, param):
    print("##############################################")
    print("Fuzzer:\t\t" + tool)
    print("Varying:\t" + param)
    tool_data = group_param(data, param)
    for v in tool_data:
        print("----------------------------------------------")
        print(param + ":\t" + v)
        print("Coverage (%):\t" + get_coverage(tool_data[v]))
        print("Bugs (%):\t" + get_rate(tool_data[v]))
        print("TTE (min):\t" + get_TTE(tool_data[v]))

def sort_values(values):
    values_int = set()
    values_str = list()
    for v in values:
        values_int.add(int(v))
    values_int = sorted(values_int)
    for v in values_int:
        values_str.append(str(v))
    return values_str

def get_param_values(param, tools):
    param_values = set()
    if param == "Cycle":
        param_t = "Cycle Proportion"
    else:
        param_t = param
    for tool in tools:
        for run in tools[tool]:
            param_values.add(run[param_t])
    if param == "Cycle":
        param_values = sort_values(param_values)
    else:
        param_values = sorted(param_values)
    return param_values

def print_measurement(metric, line_header):
    print("\nMeasure:\t" + metric)
    print(line_header)

def print_headers(param, values):
    print("Tool\t\t" + param)
    header = ""
    if param == "Size" or param == "Cycle":
        for v in values:
            header += v + "\t\t"
    else:
        for v in values:
            if v == 'Kruskal' or v == 'Prims':
                header += v + "\t\t"
            else:
                header += v + "\t"
    print("\t\t" + header)

def get_tool(data, tool, param):
    if tool == 'eclipser' or tool == 'fuzzolic':
        row = tool + "\t"
    else:
        row = tool + "\t\t"
    tool_data = group_param(data, param)
    return tool_data, row

def print_coverage(data, tool, param, values):
    tool_data, row = get_tool(data, tool, param)
    for v in values:
        if v in tool_data:
            row += get_coverage(tool_data[v])
        else:
            row += '-'
        row += '\t\t'
    print(row)

def print_bugs(data, tool, param, values):
    tool_data, row = get_tool(data, tool, param)
    for v in values:
        if v in tool_data:
            row += get_rate(tool_data[v])
        else:
            row += '-'
        row += '\t\t'
    print(row)

def print_TTE(data, tool, param, values):
    tool_data, row = get_tool(data, tool, param)
    for v in values:
        if v in tool_data:
            row += get_TTE(tool_data[v])
        else:
            row += '-'
        row += '\t\t'
    print(row)

def print_results_paper(tools, param):
    param_values = get_param_values(param, tools)
    numb_param = len(param_values)
    line_header ="########"*(2 + numb_param*2)
    line = "--------"*(2 + numb_param*2)

    # print coverage results
    print_measurement("Coverage (%)", line_header)
    print_headers(param, param_values)
    print(line)
    for tool in tools:
        print_coverage(tools[tool], tool, param, param_values)
        print(line)

    # print bugs results
    print_measurement("Bugs (%)", line_header)
    print_headers(param, param_values)
    print(line)
    for tool in tools:
        print_bugs(tools[tool], tool, param, param_values)
        print(line)

    # print TTE results
    print_measurement("TTE (min)", line_header)
    print_headers(param, param_values)
    print(line)
    for tool in tools:
        print_TTE(tools[tool], tool, param, param_values)
        print(line)

def parse_csv(summary_txt, param, time, mode):
    with open(summary_txt, 'r') as f:
        csv_reader = csv.DictReader(f)

        # filter data by time
        data = []
        for row in csv_reader:
            # if row['Number of Hours'] == time:
            data.append(row)

        # group by fuzzer
        tools = defaultdict(list)
        for row in data:
            tools[row['Tool']].append(row)

        param_list = ["Algorithm", "Size", "Cycle", "Generator"]
        # print results for each fuzzer
        if mode == 'fuzzer':
            for tool in tools:
                if param == "ALL":
                    for p in param_list:
                        print_results_fuzzer(tools[tool], tool, p)
                elif '+' in param:
                    params = param.split('+')
                    assert len(params) == 2
                    tool_data = group_param(tools[tool], params[0])
                    for first_param in tool_data:
                        print("##############################################")
                        print(params[0] + ":\t" + first_param)
                        print_results_fuzzer(tool_data[first_param], tool, params[1])
                else:
                    print_results_fuzzer(tools[tool], tool, param)

        # print results for each metric
        elif mode == 'paper':
            if param == "ALL":
                for p in param_list:
                    print_results_paper(tools, p)
            elif '+' in param:
                params = param.split('+')
                assert len(params) == 2
                first_param_values = get_param_values(params[0], tools)
                second_param_values = get_param_values(params[1], tools)
                numb_param = len(second_param_values)
                line_header ="########"*(2 + numb_param*2)
                grouped = defaultdict(list)
                for p in first_param_values:
                    for d in data:
                        if d[params[0]] == p:
                            grouped[p].append(d)
                for p in first_param_values:
                    print("\n" + line_header)
                    print("\t\t" + p)
                    print(line_header)
                    tools_grouped = defaultdict(list)
                    for row in grouped[p]:
                        tools_grouped[row['Tool']].append(row)
                    print_results_paper(tools_grouped, params[1])
            else:
                print_results_paper(tools, param)
        else:
            print("Unsupported print mode")
            exit(1)

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

def main(file_list, out_path, param, time, mode):
    f = open(out_path, 'w')
    writer = csv.writer(f)
    write_row_headers(writer)
    write_rows(writer, file_list, time)
    f.close()
    parse_csv(out_path, param, time, mode)

if __name__ == '__main__':
    global benchmark_dir
    fuzz_output_dir = sys.argv[1]
    conf = load_config(sys.argv[2])
    benchmark_dir = conf['MazeDir']
    file_list = get_coverage_files(fuzz_output_dir)
    param = sys.argv[3]
    time = sys.argv[4]
    mode = sys.argv[5]
    out_path = fuzz_output_dir + '/summary_{}h.csv'.format(time)
    main(file_list, out_path, param, time, mode)
