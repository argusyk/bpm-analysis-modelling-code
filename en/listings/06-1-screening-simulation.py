# Listing from Section 6.7.2 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

import random
import simpy

random.seed(42)                 # fixed seed: the result is reproducible
LAMBDA, MU = 3.33, 4.2      # shipments per hour: arrivals and service
waits = []

def shipment(env, xray):
    arrived = env.now
    with xray.request() as req:             # join the queue for the machine
        yield req
        waits.append(env.now - arrived)     # how long it waited
        yield env.timeout(random.expovariate(MU))

def arrivals(env, xray):
    while True:
        yield env.timeout(random.expovariate(LAMBDA))
        env.process(shipment(env, xray))

env = simpy.Environment()
xray = simpy.Resource(env, capacity=1)      # try capacity=2
env.process(arrivals(env, xray))
env.run(until=24 * 90)                      # 90 days
print(f"average wait: {sum(waits) / len(waits):.2f} h")
