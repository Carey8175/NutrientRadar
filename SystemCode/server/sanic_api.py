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


# delete ------------------------------------------------------------------------------------------------


# select ------------------------------------------------------------------------------------------------


# update ------------------------------------------------------------------------------------------------


# search ------------------------------------------------------------------------------------------------
app.add_route(login, "/api/v1/search/login", methods=['POST'])  # tags=["登录"]

# chat---------------------------------------------------------------------------------------------------


#app.add_route(document, "/api/docs", methods=['GET'])

#app.add_route(upload_weblink, "/api/local_doc_qa/upload_weblink", methods=['POST'])  # tags=["上传网页链接"]

#app.add_route(local_doc_chat, "/api/local_doc_qa/local_doc_chat", methods=['POST'])  # tags=["问答接口"]
#app.add_route(list_kbs, "/api/local_doc_qa/list_knowledge_base", methods=['POST'])  # tags=["知识库列表"]
#app.add_route(list_docs, "/api/local_doc_qa/list_files", methods=['POST'])  # tags=["文件列表"]
#app.add_route(get_total_status, "/api/local_doc_qa/get_total_status", methods=['POST'])  # tags=["获取所有知识库状态"]
#app.add_route(clean_files_by_status, "/api/local_doc_qa/clean_files_by_status", methods=['POST'])  # tags=["清理数据库"]
#app.add_route(delete_docs, "/api/local_doc_qa/delete_files", methods=['POST'])  # tags=["删除文件"]
#app.add_route(delete_knowledge_base, "/api/local_doc_qa/delete_knowledge_base", methods=['POST'])  # tags=["删除知识库"]
#app.add_route(rename_knowledge_base, "/api/local_doc_qa/rename_knowledge_base", methods=['POST'])  # tags=["重命名知识库"]


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8777, access_log=False)

