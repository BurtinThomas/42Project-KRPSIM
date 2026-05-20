import re
from class_file import Stock, Process

def parse_quantity_map(text):
    values = {}
    text = text.strip()
    if not text:
        return values
    for chunk in text.split(';'):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, qty = chunk.split(':', 1)
        values[name.strip()] = int(qty.strip())
    return values


def parse_configuration(file_content):
    stocks = {}
    processes = []
    optimizations = []
    for raw_line in file_content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        # OPTIMIZE
        if line.startswith("optimize:"):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("(") and rest.endswith(")"):
                inner = rest[1:-1].strip()
                if inner:
                    optimizations = [x.strip() for x in inner.split(';') if x.strip()]
            continue
        # STOCK
        if '(' not in line:
            name, qty = line.split(':', 1)
            stocks[name.strip()] = Stock(name.strip(), int(qty.strip()))
            continue
        # PROCESS
        match = re.match(r'^([^:]+):\((.*?)\)(?::\((.*?)\))?(?::(.*))?$', line)
        if not match:
            raise ValueError(f"Invalid process line: {line}")
        name = match.group(1).strip()
        needs_text = match.group(2)
        results_text = match.group(3) or ''
        delay_text = match.group(4) or ''
        delay_text = delay_text.strip().lstrip(':')
        process = Process(
            name,
            parse_quantity_map(needs_text),
            parse_quantity_map(results_text),
            int(delay_text) if delay_text else 0,
        )
        processes.append(process)
    return stocks, processes, optimizations