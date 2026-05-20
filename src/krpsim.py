import sys
import os
from parsing import parse_configuration
from brain import apply_process


def read_file(file_name):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(project_root, file_name)
    with open(path, 'r') as f:
        return f.read()


def main():
    try:
        file_name = sys.argv[1]
        max_cycle = int(sys.argv[2])
        content = read_file(file_name)
        stocks, processes, optimizations = parse_configuration(content)
        apply_process(processes, stocks, max_cycle, optimizations, len(stocks))
    except Exception as e:
        print(e)

main()