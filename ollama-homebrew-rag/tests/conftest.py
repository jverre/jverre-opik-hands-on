import os

# The tests never talk to an Opik server: @track and OpikTracer become no-ops.
os.environ["OPIK_TRACK_DISABLE"] = "true"
