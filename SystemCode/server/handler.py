import base64
import uuid
import logging
import json
import pandas as pd
from sanic.response import json as sanic_json
from sanic import request as sanic_request
from SystemCode.utils.general_utils import *
from SystemCode.utils.mysql_client import MySQLClient
from SystemCode.configs.basic import *
from openai import OpenAI
import datetime

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', force=True)

mysql_client = MySQLClient()


# --------------------User-------------------------
async def login(req: sanic_request):
    """
    user_name
    log in
    """
    user_name = safe_get(req, 'user_name')
    if user_name is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    status = mysql_client.check_user_exist_by_name(user_name)
    if not status:
        return sanic_json({"code": 200, "msg": f'用户名不存在，请检查！', "status": None, "user_id": None, "api_key": None, "base_url": None, "model": None, "height": None, "weight": None, "age": None, "group": None, "allergy": None})

    sql = "SELECT user_id FROM User WHERE user_name = %s"
    result = mysql_client.execute_query_(sql, (user_name,), fetch=True)
    user_id = result[0][0]

    info = mysql_client.get_chat_information(user_id)

    logging.info("[API]-[login] user_id: %s", user_id)
    return sanic_json({"code": 200, "msg": "success log in", "status": True, "user_id": user_id, "height": info[0][0], "weight": info[0][1], "age": info[0][2], "group": info[0][3], "allergy": info[0][4]})


async def add_new_user(req: sanic_request):
    """
    user_name， user_dict
    add new user into mysql
    """
    user_name = safe_get(req, 'user_name')
    user_dict = safe_get(req, 'user_dict')
    if not user_name:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    if mysql_client.check_user_exist_by_name(user_name):
        return sanic_json({"code": 2001, "status": None, "msg": f'用户名{user_name}已存在，请更换！'})

    if not user_dict:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
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
    if not isinstance(user_dict['height'], int) or not isinstance(user_dict['weight'], int) or not isinstance(user_dict['age'], int) or not isinstance(user_dict['group'], str) or not isinstance(user_dict['allergy'], str):
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
    user_id,nutrition_list
    log in
    """
    nutrition_list = safe_get(req, 'nutrition_list')
    if nutrition_list is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    result = mysql_client.analyze_nutrition_(nutrition_list)
    logging.info("[API]-[analyze nutrition] nutrition_list: %s, result: %s", nutrition_list, result)
    return sanic_json({"code": 200, "status": True, "msg": "success analyze nutrition", "result": result})


async def add_history(req: sanic_request):
    """
    user_id nutrition_dict
    nutrition_dict
    add history
    """
    user_id = safe_get(req, 'user_id')
    nutrition_dict = safe_get(req, 'nutrition_dict')
    if user_id is None or nutrition_dict is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    if not mysql_client.check_user_exist_by_id(user_id):
        return sanic_json({"code": 2001, "status": None, "msg": f'用户{user_id}不存在，请检查！'})

    if type(nutrition_dict) == str:
        try:
            nutrition_dict_str = nutrition_dict
            nutrition_dict = json.loads(nutrition_dict_str)
        except Exception as e:
            logging.error("[ERROR] nutrition_dict is not a valid json string")

    if type(nutrition_dict) != dict:
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict格式错误！request.json：{req.json}，请检查！'})

    #value in dict can not be null
    if not nutrition_dict.get('food_dict', None):
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict内容缺失！request.json：{req.json}，请检查！'})

    if not nutrition_dict.get('total_nutrition', None):
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict内容缺失！request.json：{req.json}，请检查！'})

    df = pd.read_csv(FOOD_NUTRITION_CSV_PATH)
    food_names_std = set(df['Food_name'].str.lower())
    food_names = set(nutrition_dict['food_dict'].keys())

    if len(food_names_std | food_names) != len(food_names_std):
        return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict[food_name]内容错误！request.json：{req.json}，请检查！'})

    for key in nutrition_dict['food_dict'].keys():
        nutrition_std = {'Calories', 'Protein', 'Fat', 'Carbs', 'Calcium', 'Iron', 'VC', 'VA', 'Fiber'}
        nutrition = set(nutrition_dict['food_dict'][key].keys())

        if len(nutrition_std | nutrition) != len(nutrition_std):
            return sanic_json({"code": 2002, "status": None, "msg": f'nutrition_dict[food_dict][nutrition]内容错误！request.json：{req.json}，请检查！'})

    mysql_client.add_history_(user_id, nutrition_dict)
    logging.info("[API]-[add history] user_id: %s, nutrition_dict: %s", user_id, nutrition_dict)
    return sanic_json({"code": 200, "status": True, "msg": "success add history", "user_id": user_id, "nutrition_dict": nutrition_dict})


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

    history = mysql_client.get_history_by_user_id(user_id, history_num)

    history_list = []
    for record in history:
        record_dict = {
            "user_id": record[0],
            "Datetime": record[1],
            "FoodClasses": record[2],
            "Calories": record[3],
            "Protein": record[4],
            "Fat": record[5],
            "Carbs": record[6],
            "Calcium": record[7],
            "Iron": record[8],
            "VC": record[9],
            "VA": record[10],
            "Fiber": record[11]
        }

        if isinstance(record_dict["Datetime"], datetime.datetime):
            record_dict["Datetime"] = record_dict["Datetime"].isoformat()

        history_list.append(record_dict)

    logging.info("[API]-[get history] user_id: %s, history: %s", user_id, history_list)
    return sanic_json({"code": 200, "status": True, "msg": "success get history", "history": history_list})

  
async def chat(req: sanic_request):
    """
    uer_id, messages, model
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "status": None, "msg": get_invalid_user_id_msg(user_id=user_id)})
    logging.info("[API]-[chat] user_id: %s", user_id)

    model = safe_get(req, 'model')
    if not model:
         return sanic_json({"code": 2002, "status": None, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    messages = safe_get(req, 'messages')
    if not messages:
        return sanic_json({"code": 2002, "status": None, "msg": f'Messages未传入！request.json：{req.json}，请检查！'})
    if not isinstance(messages, list):
        try:
            messages = json.loads(messages)
        except Exception as e:
            return sanic_json({"code": 2002, "status": None, "msg": f'Messages 格式错误！request.json：{req.json}，Error:{e}请检查！'})

    try:
        api_key, base_url = mysql_client.get_chat_information(user_id)[0]
    except:
        return sanic_json({"code": 2002, "status": None, "msg": f'用户{user_id}未绑定API_KEY，请绑定API信息！'})

    chat_client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    chat_response = chat_client.chat.completions.create(
        model=model,
        messages=messages
    )

    content = chat_response.choices[0].message.content

    messages.append({"role": "assistant", "content": content})

    return sanic_json({"code": 200, "status": True, "msg": "success", "data": content, "messages": messages})


async def test(req: sanic_request):
    from sanic.response import file

    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [24, 30, 22],
        'City': ['New York', 'Los Angeles', 'Chicago']
    }
    df = pd.DataFrame(data)

    # 将数据保存到Excel文件
    excel_path = 'test.xlsx'
    df.to_excel(excel_path, index=False)

    with open('test.xlsx', 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')

    # 删除临时文件
    os.remove(excel_path)

    return sanic_json({"code": 200, "status": True, "msg": "success", "data": data})

