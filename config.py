import os

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("BASE_URL", "")
API_KEY = os.getenv("API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")

MAX_STEPS = 10
TEMPERATURE = 0.1

MAX_OBSERVATION_LIMIT = 8000
