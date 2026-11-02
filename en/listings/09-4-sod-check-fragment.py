# Listing from Section 9.5.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

for case, acts in by_case.items():          # acts: activity -> set of performers
    for a, b in RULES:                       # pairs of incompatible activities
        for person in acts.get(a, set()) & acts.get(b, set()):
            violations.append((case, a, b, person))
