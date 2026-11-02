# Лістинг з підрозділу 6.8.3 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

import pm4py

log = pm4py.read_xes("aerocargo_export.xes")

# виявлення: граф безпосереднього слідування і модель індуктивним алгоритмом
dfg, starts, ends = pm4py.discover_dfg(log)
pm4py.view_dfg(dfg, starts, ends)
net, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)

# перевірка відповідності: наскільки журнал «вписується» в модель
fitness = pm4py.fitness_token_based_replay(log, net, im, fm)
print(f"пристосованість моделі: {fitness['log_fitness']:.2f}")

# варіанти процесу: скільки різних шляхів проходять відправки
variants = pm4py.get_variants(log)
print("варіантів:", len(variants))
