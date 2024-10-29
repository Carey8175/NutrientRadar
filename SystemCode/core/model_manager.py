import logging
import pandas as pd
from ultralytics import YOLO
from openai import OpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer

from SystemCode.configs.basic import *


class ModelManager:
    def __init__(self):
        self.credit_card_model = YOLO(CREDIT_CARD_MODEL_PATH)
        self.food_model = YOLO(FOOD_MODEL_PATH)
        self.nutrition_data = None
        self.load_nutrition(FOOD_NUTRITION_CSV_PATH)
        self.llm_mode = USE_QWEN
        logging.info('[ModelManager]ModelManager initialized')
        if self.llm_mode:
            self.model = AutoModelForCausalLM.from_pretrained(
                QWEN_MODEL_NAME,
                torch_dtype="auto",
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(QWEN_MODEL_NAME)

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
        logging.info('[ModelManager]Start to analyze nutrition')

        data = {"credit_card_area": 0, "food_dict": {}}

        if detect_credit_card:
            results = self.credit_card_model.predict(image)
            if results:
                results = sorted(results[0], key=lambda x: x.boxes.conf, reverse=True)[0]
                data["credit_card_area"] = (results.masks.data >= 1).sum().item()

        results = self.food_model.predict(image)

        if not results:
            return data

        logging.info('[ModelManager]Food detected: ', results[0].boxes.cls)
        logging.info('[ModelManager]Food confidence: ', results[0].boxes.conf)

        for res in sorted(results[0], key=lambda x: x.boxes.conf, reverse=True):
            if res.boxes.conf < FOOD_CONFIDENCE_THRESHOLD:
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

    def chat_qwen(self, messages):
        """
        chat with the model
        :param messages: list of
        :return:
        """
        if not self.llm_mode:
            return 'Qwen model is not enabled'

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return response

    def chat_api(self, messages):
        chat_client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )

        chat_response = chat_client.chat.completions.create(
            model=API_MODEL_NAME,
            messages=messages
        )

        content = chat_response.choices[0].message.content

        return content


if __name__ == '__main__':
    model_manager = ModelManager()
    from PIL import Image

    image = Image.open('./img_2.png')

    data = model_manager.analyze_nutrition(image, detect_credit_card=False)
    # data2 = model_manager.analyze_nutrition(image, detect_credit_card=False)

    # print(model_manager.chat_api([{"role": "user", "content": "hello"}]))
    1