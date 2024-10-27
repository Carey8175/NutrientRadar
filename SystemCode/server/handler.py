import uuid
import logging
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


async def analyze_nutrition


async def update_history


async def delete_history


async def get_history


async def get_user_info


async def update_user_info






