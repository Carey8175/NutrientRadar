import logging
import pandas as pd
from ultralytics import YOLO

from SystemCode.configs.basic import CREDIT_CARD_MODEL_PATH, FOOD_MODEL_PATH, FOOD_NUTRITION_CSV_PATH, CREDIT_CARD_AREA


class ModelManager:
    def __init__(self):
        self.credit_card_model = YOLO(CREDIT_CARD_MODEL_PATH)
        self.food_model = YOLO(FOOD_MODEL_PATH)
        self.nutrition_data = None
        self.load_nutrition(FOOD_NUTRITION_CSV_PATH)
        logging.info('[ModelManager]ModelManager initialized')

    def load_nutrition(self, nutrition_csv_path):
        """
        load nutrition data from csv file
        :param nutrition_csv_path: str
        :return: None
        """
        self.nutrition_data = pd.read_csv(nutrition_csv_path)
        logging.info('[ModelManager]nutrition data loaded')

    def predict(self, image, model_type):
        if model_type not in ['credit_card', 'food']:
            logging.error('[ModelManager]model_type not supported')
            return None

        if model_type == 'credit_card':
            return self.credit_card_model.predict(image)

        else:
            return self.food_model.predict(image)

    def analyze_nutrition(self, image, detect_credit_card=False):
        """
        analyze the nutrition of the food in the image
        :return
        {"credit_card", "food_dict", "total_nutrition"}
        """
        data = {"credit_card_area": 0, "food_dict": {}}

        if detect_credit_card:
            results = self.credit_card_model.predict(image)
            if results and results[0]:
                results = sorted(results[0], key=lambda x: x.boxes.conf, reverse=True)[0]
                data["credit_card_area"] = (results.masks.data >= 1).sum().item()

        results = self.food_model.predict(image)
        if not results:
            return data

        for res in sorted(results[0], key=lambda x: x.boxes.conf, reverse=True):
            if res.boxes.conf < 0.5:
                break

            food_area = (res.masks.data >= 1).sum().item()
            food_name = res.names[int(res.boxes[0].cls)]
            food_nutrition_df = self.nutrition_data[self.nutrition_data['Food_name'].str.lower() == food_name.lower()]

            # with credit card
            if data["credit_card_area"] > 0 and detect_credit_card:
                food_area = food_area / data["credit_card_area"] * CREDIT_CARD_AREA
                nutrition = {
                    "Calories": food_nutrition_df['Calories'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "Protein": food_nutrition_df['Protein'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "Fat": food_nutrition_df['Fat'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "Carbs": food_nutrition_df['Carbs'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "Calcium": food_nutrition_df['Calcium'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "Iron": food_nutrition_df['Iron'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "VC": food_nutrition_df['VC'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "VA": food_nutrition_df['VA'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100,
                    "Fiber": food_nutrition_df['Fiber'].values[0] * food_area * food_nutrition_df['DensityArea'].values[0] / 100
                }

            else:
                nutrition = {
                    "Calories": food_nutrition_df['Calories'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "Protein": food_nutrition_df['Protein'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "Fat": food_nutrition_df['Fat'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "Carbs": food_nutrition_df['Carbs'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "Calcium": food_nutrition_df['Calcium'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "Iron": food_nutrition_df['Iron'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "VC": food_nutrition_df['VC'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "VA": food_nutrition_df['VA'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100,
                    "Fiber": food_nutrition_df['Fiber'].values[0] * food_nutrition_df['AverageVolume'].values[0] * food_nutrition_df['AverageDensity'].values[0] / 100
                }

            if food_name in data["food_dict"]:
                for key in nutrition.keys():
                    data["food_dict"][food_name][key] += nutrition[key]
            else:
                data["food_dict"][food_name] = nutrition

        data['total_nutrition'] = {
            "Calories": sum([data["food_dict"][food_name]["Calories"] for food_name in data["food_dict"].keys()]),
            "Protein": sum([data["food_dict"][food_name]["Protein"] for food_name in data["food_dict"].keys()]),
            "Fat": sum([data["food_dict"][food_name]["Fat"] for food_name in data["food_dict"].keys()]),
            "Carbs": sum([data["food_dict"][food_name]["Carbs"] for food_name in data["food_dict"].keys()]),
            "Calcium": sum([data["food_dict"][food_name]["Calcium"] for food_name in data["food_dict"].keys()]),
            "Iron": sum([data["food_dict"][food_name]["Iron"] for food_name in data["food_dict"].keys()]),
            "VC": sum([data["food_dict"][food_name]["VC"] for food_name in data["food_dict"].keys()]),
            "VA": sum([data["food_dict"][food_name]["VA"] for food_name in data["food_dict"].keys()]),
            "Fiber": sum([data["food_dict"][food_name]["Fiber"] for food_name in data["food_dict"].keys()])
        }

        return data


if __name__ == '__main__':
    model_manager = ModelManager()
    from PIL import Image

    #image = Image.open('./img_2.png')

    import base64
    img_str = base64.b64encode(open('../img.png', 'rb').read())
    img = base64.b64decode(img_str)
    import io
    img = Image.open(io.BytesIO(img))

    data = model_manager.analyze_nutrition(img, detect_credit_card=True)
    data2 = model_manager.analyze_nutrition(image, detect_credit_card=False)

