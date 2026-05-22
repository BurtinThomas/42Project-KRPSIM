import re
import sys
from class_file import Stock
from tools import read_file
from parsing import parse_configuration


TRACE_PATTERN = re.compile(r'^(\d+):([a-zA-Z_][a-zA-Z0-9_]*)$')


def can_execute_process(process, stocks):
    for need, qty in process.needs.items():
        if need not in stocks:
            return False
        if stocks[need].get_Stock() < qty:
            return False
    return True


def consume_resources(process, stocks):
    for need, qty in process.needs.items():
        stocks[need].stock_update(-qty)


def produce_resources(process, stocks):
    for result, qty in process.results.items():
        if result not in stocks:
            stocks[result] = Stock(result, qty)
        else:
            stocks[result].stock_update(qty)


def parse_trace(content_trace):
    trace = []
    for line in content_trace.splitlines():
        line = line.strip()
        if not line:
            continue
        match = TRACE_PATTERN.match(line)
        if not match:
            raise ValueError(f"Invalid trace line: {line!r}")
        time = int(match.group(1))
        process_name = match.group(2)
        trace.append((time, process_name))
    return trace


def verify_trace(trace, stocks, processes):
    process_map = {p.nom: p for p in processes}
    pending = []
    last_start_time = 0
    last_finish_time = 0
    for current_time, process_name in trace:
        if current_time < last_start_time:
            raise ValueError(
                f"Non-monotonic time: {current_time} after {last_start_time}"
            )
        remaining = []
        for finish_time, process in sorted(pending, key=lambda x: x[0]):
            if finish_time <= current_time:
                produce_resources(process, stocks)
                last_finish_time = max(last_finish_time, finish_time)
            else:
                remaining.append((finish_time, process))
        pending = remaining
        if process_name not in process_map:
            raise ValueError(
                f"Unknown process '{process_name}' at time {current_time}"
            )
        process = process_map[process_name]
        if not can_execute_process(process, stocks):
            raise RuntimeError(
                f"Process '{process_name}' cannot execute at time "
                f"{current_time}"
            )
        consume_resources(process, stocks)
        pending.append((current_time + process.delay, process))

        last_start_time = current_time
    for finish_time, process in sorted(pending, key=lambda x: x[0]):
        produce_resources(process, stocks)
        last_finish_time = max(last_finish_time, finish_time)
    print("Trace is valid")
    print(f"\nFinal cycle: {last_finish_time}")
    print("\nFinal stocks:")
    for name in sorted(stocks.keys()):
        print(f"{name}: {stocks[name].get_Stock()}")

def main():
    try:
        if len(sys.argv) != 3:
            raise Exception(
                "Usage: python3 krpsim_verif <config_file> <trace_file>"
            )
        config_file = sys.argv[1]
        trace_file = sys.argv[2]
        content_config = read_file(config_file)
        content_trace = read_file(trace_file)
        stocks, processes, _ = parse_configuration(content_config)
        trace = parse_trace(content_trace)
        verify_trace(trace, stocks, processes)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()