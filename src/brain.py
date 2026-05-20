import heapq

from class_file import Stock


def get_stock_quantity(stocks: dict, resource: str) -> int:
	"""Return current integer quantity for a resource (0 if absent)."""
	return stocks[resource].get_Stock() if resource in stocks else 0


def consume_needs_internal(stocks: dict, needs: dict) -> None:
	"""Subtract required quantities from stocks."""
	for name, qty in needs.items():
		stocks[name].stock_update(-qty)


def produce_results_internal(stocks: dict, results: dict) -> None:
	"""Add result quantities into stocks (create Stock if missing)."""
	for name, qty in results.items():
		if name not in stocks:
			stocks[name] = Stock(name, qty)
		else:
			stocks[name].stock_update(qty)


def is_executable(process, stocks: dict) -> bool:
	"""Return True if all needs for process are satisfied by stocks."""
	for name, qty in process.needs.items():
		if get_stock_quantity(stocks, name) < qty:
			return False
	return True


def compute_total_demand(processes: list) -> dict:
	"""Compute total net demand per resource across all processes."""
	total = {}
	for p in processes:
		for r, q in p.needs.items():
			net = q - p.results.get(r, 0)
			if net > 0:
				total[r] = total.get(r, 0) + net
	return total


def compute_resource_values(processes: list, optimize_criteria: list) -> dict:
	"""Propagate optimization values backward across the process graph.

	Returns a mapping resource -> value (float) estimating importance.
	"""
	values = {r: 1.0 for r in optimize_criteria if r != "time"}
	visited = set()
	heap = [(-v, r) for r, v in values.items()]
	heapq.heapify(heap)
	while heap:
		_, resource = heapq.heappop(heap)
		if resource in visited:
			continue
		visited.add(resource)
		for p in processes:
			net_out = {r: qty - p.needs.get(r, 0) for r, qty in p.results.items() if qty > p.needs.get(r, 0)}
			if resource not in net_out:
				continue
			output_value = sum(values.get(r, 0.0) * qty for r, qty in net_out.items())
			if output_value <= 0:
				continue
			net_in = {r: q - p.results.get(r, 0) for r, q in p.needs.items() if q > p.results.get(r, 0)}
			for r, q in net_in.items():
				if r in visited or r in optimize_criteria:
					continue
				derived = output_value / q
				if derived > values.get(r, 0.0):
					values[r] = derived
					heapq.heappush(heap, (-derived, r))
	return values


def compute_gain(process, stocks: dict, running: dict, processes_by_name: dict, optimize_criteria: list, resource_values: dict, total_demand: dict) -> float:
	"""Compute heuristic gain for a process relative to optimize_criteria."""
	g = 0.0
	for res, qty in process.results.items():
		val = resource_values.get(res, 0.0)
		if val <= 0.0:
			continue
		if res not in optimize_criteria:
			demand = total_demand.get(res, 0)
			if demand == 0:
				continue
			stock_qty = get_stock_quantity(stocks, res)
			in_flight = sum(
				cnt * max(0, processes_by_name[name].results.get(res, 0) - processes_by_name[name].needs.get(res, 0))
				for name, cnt in running.items()
			)
			effective = stock_qty + in_flight
			if effective >= demand:
				continue
			val *= (demand - effective) / demand
		g += val * qty
	return g


def choose_process_to_start(executable_processes: list, stocks: dict, running: dict, all_processes: list, processes_by_name: dict, optimize_criteria: list, resource_values: dict, total_demand: dict):
	"""Choose best next process to start using gain-over-delay (with optional lookahead for 'time')."""
	if not executable_processes:
		return None
	def score(p):
		base_gain = compute_gain(p, stocks, running, processes_by_name, optimize_criteria, resource_values, total_demand)
		if "time" in optimize_criteria:
			virtual_stock = {n: Stock(n, stocks[n].get_Stock()) for n in stocks}
			for r, q in p.needs.items():
				if r in virtual_stock:
					virtual_stock[r].stock_update(-q)
				else:
					virtual_stock[r] = Stock(r, -q)
			for r, q in p.results.items():
				if r in virtual_stock:
					virtual_stock[r].stock_update(q)
				else:
					virtual_stock[r] = Stock(r, q)
			virtual_running = dict(running)
			virtual_running[p.nom] = virtual_running.get(p.nom, 0) + 1
			best_next_gain = 0.0
			best_next_delay = p.delay if p.delay > 0 else 1
			for cand in all_processes:
				if not all(get_stock_quantity(virtual_stock, r) >= q for r, q in cand.needs.items()):
					continue
				cand_gain = compute_gain(cand, virtual_stock, virtual_running, processes_by_name, optimize_criteria, resource_values, total_demand)
				if cand_gain > best_next_gain:
					best_next_gain = cand_gain
					best_next_delay = cand.delay if cand.delay > 0 else 1
			total_gain = base_gain + best_next_gain
			total_delay = p.delay + best_next_delay
			if total_delay == 0:
				return float("inf") if total_gain > 0 else 0.0
			return total_gain / total_delay
		if p.delay == 0:
			return float("inf") if base_gain > 0 else 0.0
		return base_gain / p.delay
	best = max(executable_processes, key=score)
	return best if score(best) > 0 else None


def apply_process(processes: list, stocks: dict, max_cycle: int, optimizations: list, initial_stock_count: int):
	"""Event-driven simulation: schedule finishes in a min-heap and greedily start processes."""
	current_time = 0
	event_heap = []  # (finish_time, seq, process_name)
	execution_log = []
	running = {}
	processes_by_name = {p.nom: p for p in processes}
	resource_values = compute_resource_values(processes, optimizations)
	total_demand = compute_total_demand(processes)
	seq = 0
	iterations = 0
	max_iterations = max(1000, max_cycle * 1000)
	while current_time < max_cycle and iterations < max_iterations:
		iterations += 1
		# Handle finishing processes at current_time
		while event_heap and event_heap[0][0] == current_time:
			_, _, pname = heapq.heappop(event_heap)
			proc = processes_by_name[pname]
			produce_results_internal(stocks, proc.results)
			running[pname] -= 1
			if running[pname] == 0:
				del running[pname]
		# Find executable processes now
		executable = [p for p in processes if is_executable(p, stocks)]
		while executable:
			chosen = choose_process_to_start(executable, stocks, running, processes, processes_by_name, optimizations, resource_values, total_demand)
			if chosen is None:
				break
			# Start it
			consume_needs_internal(stocks, chosen.needs)
			running[chosen.nom] = running.get(chosen.nom, 0) + 1
			finish = current_time + chosen.delay
			heapq.heappush(event_heap, (finish, seq, chosen.nom))
			seq += 1
			execution_log.append(f"{current_time}:{chosen.nom}")
			executable = [p for p in processes if is_executable(p, stocks)]
		# Termination condition
		if not running and not any(is_executable(p, stocks) for p in processes):
			break
		if not event_heap:
			break
		# Jump to next event time
		current_time = event_heap[0][0]
	# Drain remaining events to update final stocks
	while event_heap:
		finish, _, pname = heapq.heappop(event_heap)
		current_time = finish
		proc = processes_by_name[pname]
		produce_results_internal(stocks, proc.results)

	print(f"Nice file! {len(processes)} processes, {initial_stock_count} stocks, {len(optimizations)} to optimize")
	print("Main walk")
	for line in execution_log:
		print(line)
	print(f"no more process doable at time {current_time}")
	print("Stock :")
	for name in sorted(stocks):
		print(f"{name}=> {stocks[name].quantite}")
