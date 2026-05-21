import re
from class_file import Stock, Process

STOCK_PATTERN = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*):(\d+)$')

_ITEM_LIST = r'[a-zA-Z_][a-zA-Z0-9_]*:\d+(?:;[a-zA-Z_][a-zA-Z0-9_]*:\d+)*'
PROCESS_PATTERN = re.compile(
    r'^([a-zA-Z_][a-zA-Z0-9_]*)'
    r':\((' + _ITEM_LIST + r')\)'
    r':(?:\((' + _ITEM_LIST + r')\))?'
    r':(\d+)$'
)

_OPT_ITEM = r'[a-zA-Z_][a-zA-Z0-9_]*'
OPTIMIZE_PATTERN = re.compile(
    r'^optimize:\((' + _OPT_ITEM + r'(?:;' + _OPT_ITEM + r')*)\)$'
)


def parse_quantity_map(text):
    values = {}
    for chunk in text.split(';'):
        name, qty = chunk.split(':', 1)
        values[name] = int(qty)
    return values


def parse_configuration(file_content):
    stocks = {}
    processes = []
    optimizations = []
    for raw_line in file_content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('optimize:'):
            m = OPTIMIZE_PATTERN.match(line)
            if not m:
                raise ValueError(f"Invalid optimize line: {line!r}")
            optimizations = m.group(1).split(';')
            continue

        if line.count(':') >= 3:
            m = PROCESS_PATTERN.match(line)
            if not m:
                raise ValueError(f"Invalid process line: {line!r}")
            process = Process(
                m.group(1),
                parse_quantity_map(m.group(2)) if m.group(2) else {},
                parse_quantity_map(m.group(3)) if m.group(3) else {},
                int(m.group(4)),
            )
            processes.append(process)
            continue

        m = STOCK_PATTERN.match(line)
        if not m:
            raise ValueError(f"Invalid stock line: {line!r}")
        name = m.group(1)
        stocks[name] = Stock(name, int(m.group(2)))

    if not stocks or not processes or not optimizations:
        raise ValueError("Configuration must contain at least one stock, one process, and one optimization.")
    return stocks, processes, optimizations