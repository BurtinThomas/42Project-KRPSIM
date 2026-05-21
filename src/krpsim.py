import sys
from parsing import parse_configuration
from brain import apply_process
from tools import read_file, write_file


def main():
    try:
        if len(sys.argv) != 3:
            raise Exception("Usage: python3 krpsim.py <file> <max_cycle>")
        file_name = sys.argv[1]
        max_cycle = int(sys.argv[2])
        content = read_file(file_name)
        stocks, processes, optimizations = parse_configuration(content)
        initial_stock_count = len(stocks)
        stocks, processes, execution_log, current_time = apply_process(processes, stocks, max_cycle, optimizations)

        print(f"Nice file! {len(processes)} processes, {initial_stock_count} stocks, {len(optimizations)} to optimize")
        print("Main walk")
        for line in execution_log:
            write_file(file_name + "_trace.txt", line + "\n")
            print(line)
        print(f"no more process doable at time {current_time}")
        print("Stock :")
        for name in sorted(stocks):
            print(f"{name}=> {stocks[name].quantite}")

    except Exception as e:
        print(f"Error: {e}")

main()