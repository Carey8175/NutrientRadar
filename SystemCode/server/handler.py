import base64
import uuid
import logging
import json
import pandas as pd
from io import BytesIO
from PIL import Image
import pillow_heif
from sanic.response import json as sanic_json
from sanic import request as sanic_request
from SystemCode.utils.general_utils import *
from SystemCode.utils.mysql_client import MySQLClient
from SystemCode.utils.nutrient_report import create_pdf
from SystemCode.utils.nutrient_history import create_history_pdf
from SystemCode.configs.basic import *
from SystemCode.core.model_manager import ModelManager
import datetime

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', force=True)
pillow_heif.register_heif_opener()

mysql_client = MySQLClient()
modelmanager = ModelManager()


# --------------------User-------------------------
async def login(req: sanic_request):
    """
    user_name
    log in
    """
    user_name = safe_get(req, 'user_name')
    if user_name is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    logging.info("[API]-[login] user_id: %s", user_name)

    status = mysql_client.check_user_exist_by_name(user_name)
    if not status:
        return sanic_json({"code": 200, "msg": f'用户名不存在，请检查！', "status": None, "user_id": None, "api_key": None, "base_url": None, "model": None, "height": None, "weight": None, "age": None, "group": None, "allergy": None})

    sql = "SELECT user_id FROM User WHERE user_name = %s"
    result = mysql_client.execute_query_(sql, (user_name,), fetch=True)
    user_id = result[0][0]

    info = mysql_client.get_chat_information(user_id)

    return sanic_json({"code": 200, "msg": "success log in", "status": True, "user_id": user_id, "height": info[0][0], "weight": info[0][1], "age": info[0][2], "group": info[0][3], "allergy": info[0][4]})


async def add_new_user(req: sanic_request):
    """
    user_name， user_dict
    add new user into mysql
    """
    user_name = safe_get(req, 'user_name')
    user_dict = safe_get(req, 'user_dict')
    logging.info("[API]-[add new user] user_name: %s, user_dict: %s", user_name, user_dict)

    if not user_name:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    if mysql_client.check_user_exist_by_name(user_name):
        return sanic_json({"code": 2001, "status": None, "msg": f'用户名{user_name}已存在，请更换！'})

    if not user_dict:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    print(f"user_dict: {user_dict}, type: {type(user_dict)}")

    if type(user_dict) == str:
        try:
            user_dict_str = user_dict
            user_dict = json.loads(user_dict_str)
        except Exception as e:
            logging.error("[ERROR] user_dict is not a valid json string")
            return sanic_json({"code": 2003, "status": None, "msg": f'user_dict内容缺失！request.json：{req.json}，请检查！'})

    if type(user_dict) != dict:
        return sanic_json({"code": 2003, "status": None, "msg": f'user_dict格式错误！request.json：{req.json}，请检查！'})

    # value in dict can not be null
    for key in user_dict.keys():
        if key not in ['height', 'weight', 'age', 'group', 'allergy']:
            return sanic_json({"code": 2003, "status": None, "msg": f'user_dict_key错误！request.json：{req.json}，请检查！'})
        if user_dict[key] is None:
            return sanic_json({"code": 2003, "status": None, "msg": f'user_dict内容缺失！request.json：{req.json}，请检查！'})

    # value of height, weight, age should be int, group should be str, allergy should be str
    try:
        user_dict['height'] = int(user_dict['height'])
        user_dict['weight'] = int(user_dict['weight'])
        user_dict['age'] = int(user_dict['age'])
        user_dict['group'] = str(user_dict['group'])
        user_dict['allergy'] = str(user_dict['allergy'])
    except Exception as e:
        return sanic_json({"code": 2003, "status": None, "msg": f'user_dict_value错误！request.json：{req.json}，请检查！'})

    # generate user_id
    user_id = 'U' + uuid.uuid4().hex

    mysql_client.add_user_(user_id, user_dict, user_name)
    logging.info("[API]-[add new user] user_id: %s", user_id)
    return sanic_json({"code": 200, "msg": "success add user, id: {}".format(user_id), "status": True, "user_id":user_id, "user_name": user_name, "user_dict": user_dict})


async def get_user_info(req: sanic_request):
    """
    user_id
    user_info_dict : {
        "key": value}
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "status": None, "msg": get_invalid_user_id_msg(user_id=user_id)})

    user_info = mysql_client.get_user_info(user_id)[0]
    user_info_dict = {
        "user_id": user_info[0],
        "name": user_info[1],
        "height": user_info[2],
        "weight": user_info[3],
        "age": user_info[4],
        "group": user_info[5],
        "allergy": user_info[6]
    }

    return sanic_json({"code": 200, "status": True, "msg": "成功获取用户信息", "user_info": user_info_dict})


async def update_user_info(req: sanic_request):
    """
    user_id
    user_info_dict : {
        "key": value}
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "status": None, "msg": get_invalid_user_id_msg(user_id=user_id)})

    user_info_dict = safe_get(req, 'user_info_dict')
    if user_info_dict is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    if type(user_info_dict) == str:
        user_info_str = user_info_dict
        try:
            user_info_dict = json.loads(user_info_str)
        except Exception as e:
            logging.warning(f"parse user_info_dict failed: {e}")
            return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    if type(user_info_dict) != dict:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    if not user_info_dict:
        return sanic_json({"code": 2003, "status": None, "msg": "没有可更新的字段"})

    mysql_client.update_user_info(user_id, user_info_dict)
    return sanic_json({"code": 200, "status": True, "msg": "success update user info"})


async def analyze_nutrition(req: sanic_request):
    """
    user_id, img
    log in
    """
    user_id = safe_get(req, 'user_id')
    if not user_id:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "status": None, "msg": get_invalid_user_id_msg(user_id=user_id)})

    img_base64_str = safe_get(req, 'img')
    if not img_base64_str:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    use_card = safe_get(req, 'use_card')
    use_card = True if use_card == 1 else False

    logging.info("[API]-[analyze nutrition] use_card: %s", use_card)

    img = Image.open(BytesIO(base64.b64decode(img_base64_str)))
    result = modelmanager.analyze_nutrition(img, use_card)

    pdf = create_pdf(result['food_dict'], result['total_nutrition'])
    encode_pdf = base64.b64encode(pdf.read()).decode('utf-8')

    if result['food_dict']:
        # add to history
        add_history(user_id, result)
    else:
        encode_pdf = base64.b64encode(b'No food found in your photo, please take another one!').decode('utf-8')

    return sanic_json({"code": 200, "status": True, "msg": "success analyze nutrition", "data": encode_pdf})


def add_history(user_id, nutrition_dict):
    """
    user_id nutrition_dict
    nutrition_dict
    add history
    """
    if type(nutrition_dict) == str:
        try:
            nutrition_dict_str = nutrition_dict
            nutrition_dict = json.loads(nutrition_dict_str)
        except Exception as e:
            logging.error("[ERROR] nutrition_dict is not a valid json string")

    if type(nutrition_dict) != dict:
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict格式错误: {nutrition_dict}！'})

    #value in dict can not be null
    if not nutrition_dict.get('food_dict', None):
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict内容缺失！: {nutrition_dict}'})

    if not nutrition_dict.get('total_nutrition', None):
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict内容缺失: {nutrition_dict}'})

    df = pd.read_csv(FOOD_NUTRITION_CSV_PATH)
    food_names_std = set(df['Food_name'].str.lower())
    food_names = set(nutrition_dict['food_dict'].keys())

    if len(food_names_std | food_names) != len(food_names_std):
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict[food_name]内容错误！{nutrition_dict}，请检查！'})

    for key in nutrition_dict['food_dict'].keys():
        nutrition_std = {'Calories', 'Protein', 'Fat', 'Carbs', 'Calcium', 'Iron', 'VC', 'VA', 'Fiber'}
        nutrition = set(nutrition_dict['food_dict'][key].keys())

        if len(nutrition_std | nutrition) != len(nutrition_std):
            return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict[food_dict][nutrition]内容错误！request.json：{nutrition_dict}，请检查！'})

    mysql_client.add_history_(user_id, nutrition_dict)
    logging.info("[API]-[add history] user_id: %s, nutrition_dict: %s", user_id, nutrition_dict)


async def get_history(req: sanic_request):
    """
    user_id, history_num
    log in
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    if not mysql_client.check_user_exist_by_id(user_id):
        return sanic_json({"code": 2001, "status": None, "msg": f'用户{user_id}不存在，请检查！'})

    history_num = safe_get(req, 'history_num')
    if history_num is None:
        history_num = 10
    if not isinstance(history_num, int):
        try:
            history_num = int(history_num)
        except Exception as e:
            return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    # encode the history to excel
    history = mysql_client.get_history_by_user_id(user_id, history_num)
    df = pd.DataFrame(history)

    pdf = create_history_pdf(df)
    encoded_excel = base64.b64encode(pdf.read()).decode('utf-8')

    logging.info("[API]-[get history] user_id: %s", user_id)

    return sanic_json({"code": 200, "status": True, "msg": "success get history", "data": encoded_excel})


async def recommend(req: sanic_request):
    """
    user_id, model
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "status": None, "msg": get_invalid_user_id_msg(user_id=user_id)})
    logging.info("[API]-[recommend] user_id: %s", user_id)

    # get history 7 days
    history = mysql_client.get_history_by_user_id(user_id, 7)
    history_json = json.dumps(pd.DataFrame(history).to_json(orient='records'))

    food_info = pd.read_csv(FOOD_NUTRITION_CSV_PATH)
    # split to 3 parts to avoid too many data
    food_info1 = food_info.iloc[:30]
    food_info2 = food_info.iloc[30:60]
    food_info3 = food_info.iloc[60:]
    messages = [
        {"role": "system", "content": "I am a recipe recommendation system.recommend you to morrow's recipes based on your history and food nutrition info."},
        {"role": "system", "content": json.dumps(food_info1.to_json(orient='records'))},
        {"role": "system", "content": json.dumps(food_info2.to_json(orient='records'))},
        {"role": "system", "content": json.dumps(food_info3.to_json(orient='records'))},
        {"role": "user", "content": 'This is my history record: ' + history_json}
    ]
    print(messages)
    # use LLMs to recommend recipes
    if USE_QWEN:
        response = modelmanager.chat_qwen(messages)
    else:
        response = modelmanager.chat_api(messages)

    return sanic_json({"code": 200, "status": True, "msg": "success recommend", "data": response})

