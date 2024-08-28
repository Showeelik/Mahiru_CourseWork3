import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
AREAS_DIR = os.path.join(DATA_DIR, "areas.json")
EMPLOYERS_DIR = os.path.join(DATA_DIR, "employers.json")

LOGS_DIR = os.path.join(BASE_DIR, "logs")
