# Лістинг з підрозділу 6.7.2 посібника «Основи аналізу та моделювання бізнес-процесів в ІТ».

import random
import simpy

random.seed(42)                 # фіксоване зерно: результат відтворюється
LAMBDA, MU = 3.33, 4.2      # відправок на годину: надходження та обслуговування
waits = []

def shipment(env, xray):
    arrived = env.now
    with xray.request() as req:             # стати в чергу до апарата
        yield req
        waits.append(env.now - arrived)     # скільки чекали
        yield env.timeout(random.expovariate(MU))

def arrivals(env, xray):
    while True:
        yield env.timeout(random.expovariate(LAMBDA))
        env.process(shipment(env, xray))

env = simpy.Environment()
xray = simpy.Resource(env, capacity=1)      # спробуйте capacity=2
env.process(arrivals(env, xray))
env.run(until=24 * 90)                      # 90 діб
print(f"середнє очікування: {sum(waits) / len(waits):.2f} год")
