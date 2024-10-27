import os


LOG_LEVEL = 'INFO'

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CREDIT_CARD_MODEL_NAME = 'cre1.0.pt'
FOOD_MODEL_NAME = 'food1.0.pt'
CREDIT_CARD_MODEL_PATH = os.path.join(ROOT_PATH, 'sources', 'models', CREDIT_CARD_MODEL_NAME)
FOOD_MODEL_PATH = os.path.join(ROOT_PATH, 'sources', 'models', FOOD_MODEL_NAME)

FOOD_NUTRITION_CSV_PATH = os.path.join(ROOT_PATH, 'sources', 'nutrition.csv')