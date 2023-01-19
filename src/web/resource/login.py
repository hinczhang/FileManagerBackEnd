from flask_restful import Resource
from flask import Response,request
import json
import pymongo
import jwt
import time
from configparser import ConfigParser
import base64
# opt
conn = ConfigParser()
conn.read("./conf.ini")

# mongoDB
mongo_user = conn.get('mongodb','user')
mongo_passwd = conn.get('mongodb','password')
mongo_url = conn.get('mongodb','url')
mongo_port = conn.get('mongodb','port')
client = pymongo.MongoClient("mongodb://{0}:{1}@{2}:{3}/".format(mongo_user, mongo_passwd, mongo_url, mongo_port))
db = client["files"]
col = db["users"]

# token config
headers = {
  "alg": "HS256",
  "typ": "JWT"
}
salt = conn.get('key','token_key')
exp = int(time.time() + 1)

#return useful information
class Login(Resource):
    def get(self):#block get method
        pass
    def post(self):#open post method
        form = eval(str(request.data, encoding = "utf-8"))
        res = None
        if(form["mode"] == "login"):
            res = self.__login__(form['username'], form['password'], form['keep'])
        elif(form["mode"] == "token"):
            res = self.__token__(form)
        else:
            res = self.__register__(form)
        return res
    
    def __token_encoder__(self, password, username, isAdmin, keep):
        exp_time = int(time.time() + 10000000) if keep else int(time.time()+ 10000)
        payload = {"username": username, "password": password, "isAdmin": isAdmin, "keep": 1 if keep==True else 0, "exp": exp_time}
        return jwt.encode(payload=payload, key=salt, algorithm='HS256', headers=headers)

    def __token_decoder__(self, token):
        try:
            info = jwt.decode(jwt = token, key = salt, verify=True, algorithms='HS256')
            token = self.__token_encoder__(info["password"], info["username"], info["isAdmin"], info["keep"] == 1)
            return [True, token, info['username'], info['isAdmin']]
        except Exception as e:
            print(repr(e))
            return False, None, None, None
    
    def __encoder__(self, password):
        return bytes(base64.b64encode(password.encode('utf-8'))).decode()

    def __decoder__(self, password):
        return base64.b64decode(password)

    def __register__(self, form):
        query = {'username': form['username']}
        doc = list(col.find(query))
        data = None
        if len(doc) == 0:
            col.insert_one({'username': form['username'], 'password': self.__encoder__(form['password']), 'isAdmin': 0, 'isValid': 0, 'limit': 1073741824,'current': 0})
            data = json.dumps({'status': 0, 'msg': 'Registration success! Please contact the administrator for validation.'})
        else:
            data = json.dumps({'status': 1, 'msg': 'User already exists!'})
        res = Response(response=data, status=200, mimetype="application/json")#send message to frontend
        return res
    
    def __token__(self, form):
        valid, token, username, isAdmin = self.__token_decoder__(form["token"])
        data = None
        if(valid):
            data = json.dumps({'status': 0, 'msg': 'Token login success!', 'token': token, 'username': username, 'isAdmin': isAdmin})
        else:
            data = json.dumps({'status': 1, 'msg': 'Invalid token!'})
        res = Response(response = data, status = 200, mimetype="application/json")
        return res

    def __login__(self, username, password, keep):
        query = {'username': username}
        doc = list(col.find(query))
        data = None
        if len(doc) == 0:
            data = json.dumps({'status': 1, 'msg': 'User not exists!'})
            Response(response=data, status=401, mimetype="application/json")
        else:
            if(doc[0]['isValid'] == 0):
                data = json.dumps({'status': 3, 'msg': 'User not valid!'})
            else:
                flag = str(self.__decoder__(doc[0]['password']), 'utf-8')==str(password)
                if(flag):
                    data = json.dumps({'status': 0, 'msg': 'Login success!', 'username': username, 'admin': doc[0]['isAdmin'],'token': self.__token_encoder__(password, username, doc[0]['isAdmin'], keep)})
                else:
                    data = json.dumps({'status': 2, 'msg': 'Invalid password'})
                    Response(response=data, status= 401, mimetype="application/json")
        res = Response(response=data, status=200, mimetype="application/json")#send message to frontend
        return res

