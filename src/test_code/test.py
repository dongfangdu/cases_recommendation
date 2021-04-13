from datetime import datetime
import time
print(type(time.time()))
a = 1592556280.6708727
    # 1570774556514
b = "2020-06-19 16:44:40"
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a)))
print(datetime.fromtimestamp(a))
print(int(time.mktime(time.strptime(b, "%Y-%m-%d %H:%M:%S"))))