import uuid
import logging

from sanic.response import json as sanic_json
from sanic import request as sanic_request

from SystemCode.utils.mysql_client import MYSQL_HOST
from SystemCode.utils.general_utils import *
#--------------------User-------------------------

async def login
    """
    user_name
    log in
    """
    username = safe_get(req, 'username')
    password = safe_get(req, 'password')

    if not username or not password:
        return sanic_json({'status': 400, 'msg': '用户名或密码不能为空'})

    user = await get_user_by_username(username)
    if not user:
        return sanic_json({'status': 400, 'msg': '用户不存在'})

    if user['password'] != password:
        return sanic_json({'status': 400, 'msg': '密码错误'})

    return sanic_json({'status': 200, 'msg': '登录成功', 'data': user})

async def analyze_nutrition


async def update_history


async def delete_history


async def get_history


async def get_user_info


async def update_user_info






