<img src="42042015.jpg" align="right" />

# 企业微信群机器人webhook聚合  [![Awesome](badge.svg)](#)
> Enterprise WeChat group robot webhook aggregation

## 项目介绍
企业微信群机器人每分钟发送消息的限制给企业通信带来了一些挑战，限制了即时通讯的效率。为了解决这一问题，我们创建了EnterpriseBotAggregate，一个专注于企业微信群机器人Webhook聚合的开源项目。
配置.env文件中的参数，即可运行。


## 实现原理
1. 通过FastAPI提供接口，供其他项目调用。
2. 通过mysql存储每个机器人的webhook key。
3. 通过redis存储每个机器人的webhook key的每分钟发送次数。
4. 当某个机器人的webhook key每分钟发送次数达到限制时，自动切换到下一个机器人的webhook key发送消息。
5. 当所有机器人的webhook key每分钟发送次数达到限制时，暂停发送消息，直到下一分钟。

## 环境要求
- python3.x
- redis
- mysql
- FastAPI
- requests
- gunicorn

## 部署
### 本地部署
```bash
# 安装依赖
pip install -r requirements.txt
# 启动项目
python main.py
```
### docker部署
```bash
# 构建镜像
docker build -t WeChatBotHub:v1.0 .
# 启动容器
docker run -d --name WeChatBotHub -p 8000:8000 WeChatBotHub:v1.0
```

## 配置文件
```bash
# .env
# redis地址
REDIS_HOST=xxxxx
# redis端口
REDIS_PORT=6379
# redis用户
REDIS_USER=xxxxx
# redis密码
REDIS_PASSWORD=xxxxx
# redis库
REDIS_DB=0
#mysql地址
MYSQL_HOST=xxxxx
#mysql端口
MYSQL_PORT=3306
#mysql用户
MYSQL_USER=xxxxx
#mysql密码
MYSQL_PASSWORD=xxxxx
#mysql库
MYSQL_DB=xxxxx
```

## 接口文档
api文档地址：https://apifox.com/apidoc/shared-7ce7159b-4f6e-4a16-b27b-2eb6bc18f910