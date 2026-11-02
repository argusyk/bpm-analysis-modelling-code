# Listing from Section 6.8.3 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

import pm4py

log = pm4py.read_xes("aerocargo_export.xes")

# discovery: directly-follows graph and a model by the inductive miner
dfg, starts, ends = pm4py.discover_dfg(log)
pm4py.view_dfg(dfg, starts, ends)
net, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)

# conformance checking: how well the log "fits" the model
fitness = pm4py.fitness_token_based_replay(log, net, im, fm)
print(f"model fitness: {fitness['log_fitness']:.2f}")

# process variants: how many different paths shipments take
variants = pm4py.get_variants(log)
print("variants:", len(variants))
