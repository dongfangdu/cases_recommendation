# -*- coding:utf-8 -*-

from app import create_app

app = create_app("develop")
# app = create_app("product")
host = app.config.get('HOST')
port = app.config.get('PORT')
if __name__ == '__main__':
    app.run(host=host, port=port)

