import logging
from ultralytics import YOLO


class ModelManager:
    def __init__(self, model_path):
        self.credit_card_model = YOLO(model_path)
        self.food_model = YOLO(model_path)
        logging.info('[ModelManager]ModelManager initialized')

    def predict(self, image, model_type):
        if model_type not in ['credit_card', 'food']:
            logging.error('[ModelManager]model_type not supported')
            return None

        if model_type == 'credit_card':
            return self.credit_card_model.predict(image)

        else:
            return self.food_model.predict(image)

