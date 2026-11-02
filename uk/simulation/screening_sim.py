# -*- coding: utf-8 -*-
"""Імітаційна модель черги на скринінг (SimPy) з добовим профілем надходження.
Сценарії: A – як є (один апарат); B – друга лінія в години 9–13; C – слоти
доставки вирівнюють потік (той самий обсяг, рівномірніший профіль).
Запуск: python screening_sim.py  (результати -> results.json; 20 прогонів на сценарій, кілька хвилин)"""
import os, json, random, statistics
import simpy

HERE = os.path.dirname(os.path.abspath(__file__))
PER_DAY, MU, DAYS = 80, 4.2, 90
PEAKY = [.85]*6 + [1.0]*4 + [1.15]*2 + [1.05]*6 + [.9]*6          # надходження на скринінг (розд. 6: 3,33/год, пік ~4/год)
FLAT = [.9]*6 + [1.0]*12 + [.95]*6                               # після запровадження слотів доставки

REPS = 20                                                    # кількість незалежних прогонів

def run_once(profile, extra_lane_hours=(), seed=1):
    random.seed(seed)
    env = simpy.Environment()
    lane1 = simpy.Resource(env, capacity=1)
    lane2 = simpy.Resource(env, capacity=1)
    waits = []
    rates = [PER_DAY * w / sum(profile) for w in profile]         # відправок на годину
    lam_max = max(rates)

    def shipment():
        t0 = env.now
        hour = int(env.now) % 24
        use2 = hour in extra_lane_hours and len(lane2.queue) + lane2.count < len(lane1.queue) + lane1.count
        res = lane2 if use2 else lane1
        with res.request() as req:
            yield req
            waits.append(env.now - t0)
            yield env.timeout(random.expovariate(MU))

    def arrivals():                       # нестаціонарний пуассонівський потік методом проріджування
        while True:
            yield env.timeout(random.expovariate(lam_max))
            if random.random() < rates[int(env.now) % 24] / lam_max:
                env.process(shipment())

    env.process(arrivals())
    env.run(until=24 * DAYS)
    q = sorted(waits)
    return statistics.mean(q), q[int(0.9 * len(q))], sum(w > 2 for w in q) / len(q), len(q)

def run(profile, extra_lane_hours=()):
    """REPS прогонів з різними зернами; ті самі зерна для всіх сценаріїв (спільні випадкові числа)."""
    reps = [run_once(profile, extra_lane_hours, seed) for seed in range(1, REPS + 1)]
    means = [r[0] for r in reps]
    half = 2.093 * statistics.stdev(means) / REPS ** 0.5         # t(0,975; 19) – 95 % довірчий інтервал
    return {"mean_h": round(statistics.mean(means), 2), "ci95_h": round(half, 2),
            "p90_h": round(statistics.mean(r[1] for r in reps), 2),
            "share_over_2h": round(statistics.mean(r[2] for r in reps), 3),
            "n": round(statistics.mean(r[3] for r in reps)), "runs": REPS}

if __name__ == "__main__":
    R = {"A: як є": run(PEAKY), "B: друга лінія 9-13": run(PEAKY, extra_lane_hours=range(9, 13)),
         "C: слоти доставки": run(FLAT), "B+C разом": run(FLAT, extra_lane_hours=range(9, 13))}
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    for k, v in R.items():
        print(f"{k:22s} середнє {v['mean_h']:.2f} ± {v['ci95_h']:.2f} год, P90 {v['p90_h']:.2f} год, понад 2 год: {v['share_over_2h']:.1%}")
