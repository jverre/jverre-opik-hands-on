import os
import pathlib
import sys

# Keep unit tests offline: no traces are sent even if Opik is configured.
os.environ.setdefault("OPIK_TRACK_DISABLE", "true")
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
