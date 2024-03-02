import sys

def parse_log(log_content):
    data = {}
    lines = log_content.strip().split('\n')
    current_fuzzer = None
    for line in lines:
        if 'Fuzzer:' in line:
            current_fuzzer = line.split(':')[1].strip()
            data[current_fuzzer] = {}
        elif 'Generator:' in line:
            current_generator = line.split(':')[1].strip()
            data[current_fuzzer][current_generator] = {}
        elif 'Coverage (%):' in line:
            data[current_fuzzer][current_generator]['Coverage (%)'] = line.split(':')[1].strip()
        elif 'Bugs (%):' in line:
            data[current_fuzzer][current_generator]['Bugs (%)'] = line.split(':')[1].strip()
        elif 'TTE (h):' in line:
            data[current_fuzzer][current_generator]['TTE (h)'] = line.split(':')[1].strip()
    return data

def format_to_markdown(data):
    table_header = "| CVE             | Fuzzer   | Coverage (%) | Bugs (%) | TTE (h) |\n"
    table_divider = "|-----------------|----------|--------------|----------|---------|\n"
    table = table_header + table_divider
    # Sorting the data
    fuzzers = sorted(data.keys())
    generators = sorted(set(gen for fuzz_data in data.values() for gen in fuzz_data))
    # Creating the table rows for each generator
    for gen in generators:
        for fuzzer in fuzzers:
            if gen in data[fuzzer]:
                coverage = data[fuzzer][gen]['Coverage (%)']
                bugs = data[fuzzer][gen]['Bugs (%)']
                tte = data[fuzzer][gen]['TTE (h)']
                table += f"| {gen} | {fuzzer} | {coverage} | {bugs} | {tte} |\n"
            else:
                table += f"| {gen} | {fuzzer} | - | - | - |\n"
    return table

if __name__ == '__main__':
    log_fp = sys.argv[1]
    with open(log_fp, 'r') as f:
        log_data = f.read()
    parsed_data = parse_log(log_data)
    markdown_table = format_to_markdown(parsed_data)
    with open(log_fp, 'w') as f:
        f.write(markdown_table)
