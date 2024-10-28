import sys
from SystemCode.configs.basic import *

from SystemCode.server.handler import *
from sanic import Sanic
from sanic import response as sanic_response
import argparse
from sanic.worker.manager import WorkerManager

sys.path.append(ROOT_PATH)
WorkerManager.THRESHOLD = 6000

# 接收外部参数mode
parser = argparse.ArgumentParser()
# mode必须是local或online
parser.add_argument('--mode', type=str, default='local', help='local or online')
# 检查是否是local或online，不是则报错
args = parser.parse_args()
if args.mode not in ['local', 'online']:
    raise ValueError('mode must be local or online')

app = Sanic("ArchiveFlow")
# 设置请求体最大为 400MB
app.config.REQUEST_MAX_SIZE = 400 * 1024 * 1024


# CORS中间件，用于在每个响应中添加必要的头信息
@app.middleware("response")
async def add_cors_headers(request, response):
    # response.headers["Access-Control-Allow-Origin"] = "http://10.234.10.144:5052"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"  # 如果需要的话


@app.middleware("request")
async def handle_options_request(request):
    if request.method == "OPTIONS":
        headers = {
            # "Access-Control-Allow-Origin": "http://10.234.10.144:5052",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"  # 如果需要的话
        }
        return sanic_response.text("", headers=headers)


# add ---------------------------------------------------------------------------------------------------
app.add_route(add_history, "/api/v1/add/history", methods=['POST'])  # tags=["添加历史记录"]
app.add_route(add_new_user, "/api/v1/add/new_user", methods=['POST'])  # tags=["添加用户"]

# delete ------------------------------------------------------------------------------------------------


# select ------------------------------------------------------------------------------------------------

# update ------------------------------------------------------------------------------------------------
app.add_route(update_user_info, "/api/v1/update/user_info", methods=['POST'])  # tags=["更新用户信息"]

# search ------------------------------------------------------------------------------------------------
app.add_route(login, "/api/v1/login", methods=['POST'])  # tags=["登录"]
app.add_route(get_history, "/api/v1/search/history", methods=['POST'])  # tags=["获取历史记录"]
app.add_route(get_user_info, "/api/v1/search/user_info", methods=['POST'])  # tags=["获取用户信息"]


# chat---------------------------------------------------------------------------------------------------
app.add_route(recommend, "/api/v1/chat/recommend", methods=['POST'])  # tags=["推荐"]
app.add_route(analyze_nutrition, "/api/v1/chat/analyze_nutrition", methods=['POST'])  # tags=["分析营养"]

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=18080, access_log=False)

