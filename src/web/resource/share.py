from flask_restful import Resource
from flask import Response, request, send_file
import json
from configparser import ConfigParser
import jwt
from bson.objectid import ObjectId
import os
import time

# opt
conn = ConfigParser()
conn.read("./conf.ini")
ROOT_PATH = '/home/hinczhang/fileDB/'

# token config
headers = {
  "alg": "HS256",
  "typ": "JWT"
}
salt = conn.get('key','token_key')


def validate_user_token(token, username):
    try:
        info = jwt.decode(jwt = token, key = salt, verify=True, algorithms='HS256')
        if username == info["username"]:
            return True
        else:
            return False
    except Exception as e:
        print(repr(e))
        return False

class ShareFiles(Resource):
    def get(self):
        token = request.args.get('token')
        res = None
        try:
            info = jwt.decode(jwt = token, key = salt, verify=True, algorithms='HS256')
            path = info['path']
            if os.path.exists(ROOT_PATH + path):
                return send_file(ROOT_PATH + path, as_attachment=True)
            else:
                return 'Forbidden: File does not exist!', 403
        except Exception as e:
            print(repr(e))
            return 'Forbidden: Link expired.', 403

    def post(self):
        form = eval(str(request.data, encoding = "utf-8"))
        username = form['username']
        res = None
        if not validate_user_token(form['token'], username):
            res = Response(response = json.dumps({'status': 2, 'msg': 'Invalid operations! Will come back to the login page.'}), status = 200, mimetype="application/json")
        else:
            exp_time = int(time.time() + 60*60*24*7)
            payload = {"username": username, "path": form['path'], "exp": exp_time}
            token = jwt.encode(payload=payload, key=salt, algorithm='HS256', headers=headers)
            res = Response(response = json.dumps({'status': 0, 'msg': 'Share successfully!', 'token': token}), status = 200, mimetype="application/json")
        return res