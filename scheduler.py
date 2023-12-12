import json
import time
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from db import redis_host, redis_port, redis_user, redis_password, redis_db, get_db, get_redis
from datetime import datetime
import threading

interval_task = {
    "jobstores": {
        "redis": RedisJobStore(host=redis_host, port=redis_port, username=redis_user, password=redis_password,
                               db=redis_db)
    },
    "executors": {
        "default": ThreadPoolExecutor(10)
    },
    "job_defaults": {
        # 任务默认执行器
        "coalesce": False,
        # 最大并发数
        "max_instances": 3
    },
}


# 定义定时任务
def clear_message():
    # 使用多线程执行定时任务
    print('开始根据机器人的数量创建线程')
    # 获取机器人数量
    with get_db() as db:
        sql = "select count(*) from botinformation where BotStatus=1"
        db.execute(sql)
        bot_count = db.fetchone()[0]
    if bot_count == 0:
        print('未创建任何机器人,机器人数量为0')
        return
    # 创建线程
    for i in range(bot_count):
        t = threading.Thread(target=clear_message_thread, args=(i,))
        t.start()
    print("线程创建完成,共创建", bot_count, "个线程")


def clear_message_thread(thread_id):
    thread_id += 1
    # 获取当前线程的数字
    time.sleep(thread_id / 10)
    # 获取机器人信息
    with get_db() as db:
        sql = "select * from botinformation where BotStatus=1 limit %s,1"
        db.execute(sql, (thread_id - 1,))
        bot = db.fetchone()
    bot_name = bot[1]
    bot_key = bot[2]

    with get_redis() as redis:
        # 循环获取消息
        while True:
            # 获取消息
            message = redis.rpop("message")
            # 判断消息是否为空
            if message is None:
                break
            # 把消息转换为json格式
            message = json.loads(message)
            # 获取消息类型
            msgtype = message["msgtype"]
            # 获取消息内容
            content = message["content"]
            # 发送消息
            url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={bot_key}"
            data = {
                "msgtype": msgtype,
                "text": {
                    "content": content
                }
            }
            data = json.dumps(data)
            response = json.loads(requests.post(url, data=data).text)
            # 判断是否发送成功
            if response["errcode"] != 0:
                print(f"{bot_name}消息发送失败,错误代码:{response['errcode']},错误信息:{response['errmsg']}")
                # 把消息重新放入队列
                redis.lpush("message", json.dumps(message))
                break
    print(f"线程{thread_id}执行完成")


scheduler = AsyncIOScheduler(**interval_task)

# 添加定时任务
scheduler.add_job(func=clear_message, trigger='interval', seconds=70, id='get_access_token',
                  next_run_time=datetime.now())
