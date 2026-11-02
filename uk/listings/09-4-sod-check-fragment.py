# Лістинг з підрозділу 9.5.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

for case, acts in by_case.items():          # acts: дія -> множина виконавців
    for a, b in RULES:                       # пари несумісних дій
        for person in acts.get(a, set()) & acts.get(b, set()):
            violations.append((case, a, b, person))
