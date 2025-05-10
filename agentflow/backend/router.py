# router.py

import random
from .models import Task

HUMANS = ["Jane Doe", "Carlos R.", "Priya N."]

def route(task: Task) -> Task:
    if task.routed_to == "human":
        task.owner = random.choice(HUMANS)
    return task
