import redis
import mysql.connector
import os
from dotenv import load_dotenv, find_dotenv
from contextlib import contextmanager

load_dotenv(find_dotenv('.env'))
env_dist = os.environ

# load environment variables
mysql_host = env_dist.get('MYSQL_HOST')
mysql_port = env_dist.get('MYSQL_PORT')
mysql_user = env_dist.get('MYSQL_USER')
mysql_password = env_dist.get('MYSQL_PASSWORD')
mysql_db = env_dist.get('MYSQL_DB')

redis_host = env_dist.get('REDIS_HOST')
redis_port = env_dist.get('REDIS_PORT')
redis_user = env_dist.get('REDIS_USER')
redis_password = env_dist.get('REDIS_PASSWORD')
redis_db = env_dist.get('REDIS_DB')


def get_db_connection():
    connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db
    )
    return connection


@contextmanager
def get_db():
    connection = get_db_connection()
    db = connection.cursor()
    try:
        yield db
    finally:
        db.close()
        connection.close()


def get_redis_pool():
    pool = redis.ConnectionPool(
        host=redis_host,
        port=redis_port,
        username=redis_user,
        password=redis_password,
        db=redis_db
    )
    return pool


pool = get_redis_pool()


@contextmanager
def get_redis():
    redis_client = redis.Redis(connection_pool=pool)
    try:
        yield redis_client
    finally:
        redis_client.close()
        pool.disconnect()
