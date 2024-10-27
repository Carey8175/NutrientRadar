import uuid
import logging
import json
from sanic.response import json as sanic_json
from sanic import request as sanic_request
from SystemCode.utils.mysql_client import MYSQL_HOST
from SystemCode.utils.general_utils import *
from SystemCode.utils import mysql_client

mysql_client = mysql_client.MySQLClient()
#--------------------User-------------------------

async def login(req: sanic_request):
    """
    user_name
    log in
    """
    user_name = safe_get(req, 'user_name')
    if user_name is None:
        return sanic_json({"code": 2002, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    if mysql_client.check_user_exist_by_name(user_name):
        return sanic_json({"code": 2001, "msg": f'用户名{user_name}已存在，请更换！'})
    # generate user_id
    user_id = 'U' + uuid.uuid4().hex

    mysql_client.add_user_(user_id, user_name)
    logging.info("[API]-[add new user] user_id: %s", user_id)
    return sanic_json({"code": 200, "msg": "success add user, id: {}".format(user_id), "user_id": user_id})

async def get_user_info(req: sanic_request):
    """
    user_id
    user_info_dict : {
        "key": value}
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})

    user_info = mysql_client.get_user_info(user_id)[0]
    user_info_dict = {
        "user_id": user_info[0],
        "name": user_info[1],
        "api_key": user_info[2],
        "base_url": user_info[3],
        "model": user_info[4],
        "height": user_info[5],
        "weight": user_info[6],
        "age": user_info[7],
        "group": user_info[8],
        "allergy": user_info[9]
    }

    return sanic_json({"code": 200, "msg": "成功获取用户信息", "user_info": user_info_dict})

async def update_user_info(req: sanic_request):
    """
    user_id
    user_info_dict : {
        "key": value}
    """
    user_id = safe_get(req, 'user_id')
    if user_id is None:
        return sanic_json({"code": 2002, "msg": f'输入非法！request.json：{req.json}，请检查！'})
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})

    user_info_dict = safe_get(req, 'user_info_dict')
    if user_info_dict is None:
        return sanic_json({"code": 2002, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    if type(user_info_dict) == str:
        user_info_str = user_info_dict
        try:
            user_info_dict = json.loads(user_info_str)
        except Exception as e:
            logging.warning(f"parse user_info_dict failed: {e}")
            return sanic_json({"code": 2002, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    if type(user_info_dict) != dict:
        return sanic_json({"code": 2002, "msg": f'输入非法！request.json：{req.json}，请检查！'})

    if not user_info_dict:
        return sanic_json({"code": 2003, "msg": "没有可更新的字段"})

    mysql_client.update_user_info( user_id, user_info_dict )
    return sanic_json({"code": 200, "msg": "success update user name"})

# async def analyze_nutrition(req: sanic_request):