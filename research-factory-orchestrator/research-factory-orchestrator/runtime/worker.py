"""RFO bounded component wrapper: worker.py.

Compatibility wrapper around scripts.rfo_v18_core until full decomposition.
"""

# Import dynamically only when used to avoid entrypoint side effects.
def component_boundary():
    return "worker"
