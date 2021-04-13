from flask import Blueprint
import subprocess

command = "mongo-connector -c /home/user/linjr/cases_recommendation/cfg/config.json"
child1 = subprocess.Popen(command, shell=True)

#1. 创建蓝图对象
ind = Blueprint("ind", __name__)

# 切记：一定要让模块发现views.py文件
from .views import *
