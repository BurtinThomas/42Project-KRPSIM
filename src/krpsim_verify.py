
import re
from class_file import Stock
import sys
from tools import read_file
from parsing import parse_configuration


TRACE_PATTERN = re.compile(r'^(\d+):([a-zA-Z_][a-zA-Z0-9_]*)$')

def check_if_process_and_quantite_exists(processes_name_trace, processes, stocks, time):
    for p in processes:
        if p.nom == processes_name_trace:
            for need in p.needs:
                if need not in stocks:
                    print(f"Process {processes_name_trace} not found in configuration")
                    return False
                elif stocks[need].get_Stock() < p.needs[need]:
                    print(f"Insufficient stock for {need}, needed {p.needs[need]}, available {stocks[need].get_Stock()} at time {time}")
                    return False
                else:
                    print(f"Updating stock for {need}, consumed {p.needs[need]}, available {stocks[need].get_Stock()} at time {time}")
                    stocks[need].stock_update(-p.needs[need])
    return True

def update_stocks(content_trace, processes, stocks, time):
    for line in content_trace.splitlines():
        time_trace = int(line.split(':')[0])
        processes_name_trace = line.split(':')[1]
        if time == time_trace:
            for p in processes:
                if p.nom == processes_name_trace:
                    for result in p.results:
                        if result not in stocks:
                            stocks[result] = Stock(result, p.results[result])
                        else:
                            stocks[result].stock_update(p.results[result])
        

def verif(content_trace, stocks, processes):
    time = 0
    for line in content_trace.splitlines():
        m = TRACE_PATTERN.match(line)
        if not m:
            raise ValueError(f"Invalid trace line: {line!r}")
        time_trace = int(line.split(':')[0])
        processes_name_trace = line.split(':')[1]
        if time < time_trace:
            update_stocks(content_trace, processes, stocks, time)
            time = time_trace
        if not check_if_process_and_quantite_exists(processes_name_trace, processes, stocks, time):
            return
    print("Trace is valid")



def main():
    try:
        if len(sys.argv) != 3:
            raise Exception("Usage: python3 krpsim_verif <file> <result_to_test>")
        file_name = sys.argv[1]
        result_to_test = sys.argv[2]
        content_file = read_file(file_name)
        content_trace = read_file(result_to_test)
        stocks, processes, _ = parse_configuration(content_file)
        verif(content_trace, stocks, processes)
    except Exception as e:
        print(f"Error: {e}")

main()