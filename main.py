import json
import uvicorn
import logging
from fastapi import FastAPI, Depends, Body
from contextlib import asynccontextmanager
from mysql.connector import cursor

import schemas
from db import get_db, get_redis, log_path
from scheduler import scheduler
import random
import string
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
fh = logging.FileHandler(filename=log_path)
formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s"
)
fh.setFormatter(formatter)
  # 将日志输出至文件,编码为utf-8
fh.encoding = 'utf-8'
logger.addHandler(fh)
logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('启动调度器')
    scheduler.start()
    yield
    logger.info('关闭调度器')
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response

# 获取机器人列表
@app.get("/robot/list", response_model=schemas.RobotDataResponse, tags=["robot"], summary="获取机器人列表")
def robot_list(db: cursor = Depends(get_db)):
    with db as db_client:
        db_client.execute("SELECT * FROM robot_information")
        result = db_client.fetchall()
    if result:
        data = [dict(zip(["BotID", "BotName", "BotKey", "BotStatus", "MessageCount", "CreatedAt"], row)) for row in
                result]
        return {"code": 200, "msg": "success", "data": data}
    else:
        return {"code": 400, "msg": "failed", "data": "null"}


# 新增机器人
@app.post("/robot/add", response_model=schemas.RobotDataResponseInfo, tags=["robot"], summary="新增机器人")
def robot_add(
        bot_name: str = Body(..., embed=True),
        bot_key: str = Body(..., embed=True),
        db: cursor = Depends(get_db)
):
    with db as db_client:
        db_client.execute("INSERT INTO robot_information (BotName, BotKey) VALUES (%s, %s)", (bot_name, bot_key))
        # 数据插入后，需要commit才能生效
        db_client.execute("commit")
        db_client.execute("SELECT * FROM robot_information WHERE BotName = %s", (bot_name,))
        result = db_client.fetchone()
    if result:
        data = dict(zip(["BotID", "BotName", "BotKey", "BotStatus", "MessageCount", "CreatedAt"], result))
        return {"code": 200, "msg": "success", "data": data}
    else:
        return {"code": 400, "msg": "failed", "data": "null"}


# 获取机器人信息
@app.get("/robot/info", tags=["robot"], summary="获取机器人信息")
def robot_info(bot_id: int, db: cursor = Depends(get_db)):
    with db as db_client:
        db_client.execute("SELECT * FROM robot_information WHERE BotID = %s", (bot_id,))
        result = db_client.fetchone()
    if result:
        data = dict(zip(["BotID", "BotName", "BotKey", "BotStatus", "MessageCount", "CreatedAt"], result))
        return {"code": 200, "msg": "success", "data": data}
    else:
        return {"code": 400, "msg": "failed", "data": "null"}


# 删除机器人
@app.delete("/robot/delete", tags=["robot"], summary="删除机器人")
def robot_delete(bot_id: int, db: cursor = Depends(get_db)):
    with db as db_client:
        db_client.execute("SELECT * FROM robot_information WHERE BotID = %s", (bot_id,))
        result = db_client.fetchone()
        if result:
            db_client.execute("DELETE FROM robot_information WHERE BotID = %s", (bot_id,))
            db_client.execute("commit")
            return {"code": 200, "msg": "success", "data": "null"}
        else:
            return {"code": 400, "msg": "failed", "data": "null"}


# 随机获取机器人,要求机器人状态为1,并且消息数小于20
@app.get("/robot/random", tags=["robot"], summary="随机获取机器人")
def robot_random(db: cursor = Depends(get_db)):
    with db as db_client:
        db_client.execute(
            "SELECT * FROM robot_information WHERE BotStatus = 1 AND MessageCount < 20 ORDER BY RAND() LIMIT 1")
        result = db_client.fetchone()
    if result:
        data = dict(zip(["BotID", "BotName", "BotKey", "BotStatus", "MessageCount", "CreatedAt"], result))
        return {"code": 200, "msg": "success", "data": data}
    else:
        return {"code": 400, "msg": "failed", "data": "null"}


# 发送消息, 把消息存入redis
@app.post("/message/send", tags=["message"], summary="发送消息", response_model_exclude_unset=True)
async def message_send(
        msgtype: str = Body(..., embed=True),
        content: str = Body(..., embed=True),
        redis: cursor = Depends(get_redis)
):
    # 判断消息类型是否为text或markdown,如果不是则返回错误
    if msgtype != "text" and msgtype != "markdown":
        return {"code": 400, "msg": "failed", "data": "msg type error"}
    # 判断content是否为空,如果为空则返回错误
    if not content:
        return {"code": 400, "msg": "failed", "data": "content is null"}
    # 判断消息长度是否超过2048,如果超过则返回错误
    if len(content) > 2048:
        return {"code": 400, "msg": "failed", "data": "content length error"}

    # 拼接消息信息
    message = {
        "msgtype": msgtype,
        "content": content
    }
    # 把消息转换为json格式
    message = json.dumps(message)
    with redis as redis_client:
        redis_client.lpush("message", message)
        # 获取队列长度,即消息数
        message_count = redis_client.llen("message")
    return {"code": 200, "msg": "success", "message_count": message_count}


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
