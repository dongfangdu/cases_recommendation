from flask import Blueprint

#1. 创建蓝图对象
ele_ext = Blueprint("ele_ext", __name__)

# 切记：一定要让模块发现views.py文件
from .views import *
