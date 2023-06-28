from flask_restful import Resource
from flask import Response,request
import json
import pymongo
from configparser import ConfigParser
import jwt
from bson.objectid import ObjectId
import glob
import os
import shutil
import datetime
import base64
import pytz

eastern_timezone = pytz.timezone('Asia/Shanghai')


# opt
conn = ConfigParser()
conn.read("./conf.ini")
ROOT_PATH = '/home/hinczhang/fileDB/'
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

def validate_token(token, username):
    try:
        info = jwt.decode(jwt = token, key = salt, verify=True, algorithms='HS256')
        if username == info["username"]:
            return True
        else:
            return False
    except Exception as e:
        print(repr(e))
        return False

def validate_admin(token, username):
    try:
        info = jwt.decode(jwt = token, key = salt, verify=True, algorithms='HS256')
        if username == info["username"] and info["isAdmin"] == 1:
            return True
        else:
            return False
    except Exception as e:
        print(repr(e))
        return False

class ManageFiles(Resource):
    def get(self):#block get method
        pass
    def post(self):#open post method
        form = None
        try:
            form = eval(str(request.data, encoding = "utf-8"))
        except:
            form = request.form.to_dict()
        res = None
        print(form)
        if validate_token(form["token"], form["username"]):
            if(form["mode"] == "add"):
                f = request.files.to_dict()['files']
                res = self.__add_files__(form, f)
            elif(form["mode"] == "search"):
                res = self.__search_files_(form)
            elif(form["mode"] == "delete"):
                return self.__delete_files__(form)
            elif(form["mode"] == "update_password"):
                return self.__update_password__(form)
            elif(form["mode"] == "download"):
                return self.__download_file__(form)
            elif(form["mode"] == "create"):
                return self.__create_dir__(form)
            elif(form["mode"] == "get_info"):
                return self.__get_info__(form)
            elif validate_admin(form["token"], form["username"]):
                if(form["mode"] == "confirm_user"):
                    return self.__confirm_user__(form)
                elif(form["mode"] == "delete_user"):
                    return self.__delete_user__(form)
                elif(form["mode"] == "update_limit"):
                    return self.__update_limit__(form)
                elif(form["mode"] == "update_admin"):
                    return self.__update_admin__(form)
                elif(form["mode"] == "get_user"):
                    return self.__get_user__()
            else:
                res = Response(response = json.dumps({'status': 1, 'msg': 'Invalid mode! Please contact the backend developer'}), status = 200, mimetype="application/json")  
        else:
            res = Response(response = json.dumps({'status': 2, 'msg': 'Invalid operations! Will come back to the login page.'}), status = 200, mimetype="application/json")
        return res

    def __get_info__(self, form):
        username = form["username"]
        try:
            doc = col.find({'username': username})[0]
            doc.pop("_id")
            doc.pop("password")
            return Response(response = json.dumps({'status': 0, 'msg': 'Information got!', 'info': doc}), status = 200, mimetype="application/json")
        except Exception as e:
            return Response(response = json.dumps({"msg": "Database Error!", "status": 2}), status = 200, mimetype="application/json")

    def __update_password__(self, form):
        current_password = form["c_pass"]
        new_password = form["n_pass"]
        username = form["username"]
        try:
            doc = col.find({'username': username})[0]
            if str(base64.b64decode(doc["password"]), 'utf-8') == current_password:
                col.update_one({'username': username}, {"$set":{'password': bytes(base64.b64encode(new_password.encode('utf-8'))).decode()}})
                return Response(response = json.dumps({"msg": "Update successfully!!", "status": 0}), status = 200, mimetype="application/json")
            else:
                return Response(response = json.dumps({"msg": "Incorrect password!", "status": 1}), status = 200, mimetype="application/json")
        except Exception as e:
            return Response(response = json.dumps({"msg": "Database Error!", "status": 2}), status = 200, mimetype="application/json")
        

    def __add_files__(self, form, file):
        current_path = os.path.join(ROOT_PATH, form["path"])
        if os.path.exists(os.path.join(current_path, file.filename)):
            return Response(response = json.dumps({'status': 2, 'msg': 'File already exists!'}), status = 200, mimetype="application/json")
        if not os.path.exists(os.path.join(ROOT_PATH, form["username"], 'tmp')):
            os.mkdir(os.path.join(ROOT_PATH, form["username"], 'tmp'))
        tmp_path = os.path.join(ROOT_PATH, form["username"], 'tmp', file.filename)
        try:
            file.save(tmp_path)
            file_length = os.stat(tmp_path).st_size
            doc = col.find({'username': form["username"]})[0]
            if(doc['current'] + file_length >= doc['limit']):
                return Response(response = json.dumps({'status': 4, 'msg': 'Oversize Error'}), status = 200, mimetype="application/json")
            else:
                col.update_one({'username': form["username"]}, {"$set":{'current': doc['current'] + file_length}})
                shutil.move(tmp_path, os.path.join(current_path, file.filename))
                tmp_res = Response(response = json.dumps({"msg": "Upload data successfully!", "status": 0}), status = 200, mimetype="application/json")
                tmp_res.headers.add('Access-Control-Allow-Origin', '*')
                return tmp_res
        except Exception as e:
            print(repr(e))
            if os.path.exists(os.path.join(current_path, file.filename)):
                os.remove(os.path.join(current_path, file.filename))
            return Response(response = json.dumps({'status': 3, 'msg': 'Database Error'}), status = 200, mimetype="application/json")

    def __search_files_(self, form):
        current_path = os.path.join(ROOT_PATH, form["path"])      
        current_path = current_path + '/*'
        files = glob.glob(current_path)
        files_info = []
        for file in files:
            info = {}
            create_time = datetime.datetime.fromtimestamp(os.path.getctime(file))
            create_time = create_time.astimezone(eastern_timezone)
            info["date"] = create_time.strftime('%Y-%m-%d')
            info["time"] = create_time.strftime('%H:%M:%S')
            info["name"] = file.split('/')[-1]
            if  os.path.isdir(file):
                info["type"] = 'dir'
                info["size"] = -1
            else:
                info["type"] = 'file'
                info["size"] = os.path.getsize(file)
            files_info.append(info)
        return Response(response = json.dumps({"data": files_info, "msg": "Get data successfully!", "status": 0}), status = 200, mimetype="application/json")

    def __download_file__(self, form):
        current_path = os.path.join(ROOT_PATH, form["path"], form["name"])
        file = open(current_path, "rb").read()
        response = Response(file, content_type='application/octet-stream')
        response.headers['Content-disposition'] = 'attachment; filename=%s' % form["name"].encode("utf-8").decode("latin1")
        return response
        
    def __delete_files__(self, form):
        current_path = os.path.join(ROOT_PATH, form["path"])
        try:
            if form["path"] == 'tmp':
                return Response(response = json.dumps({"msg": "Delete not allowed!", "status": 2}), status = 200, mimetype="application/json")
            volume = os.stat(os.path.join(current_path, form["file"])).st_size
            if form["type"] == 'dir':
                shutil.rmtree(os.path.join(current_path, form["file"]))
            else:
                os.remove(os.path.join(current_path, form["file"]))
                doc = col.find({'username': form["username"]})[0]
                col.update_one({'username': form["username"]}, {"$set":{'current': doc['current'] - volume}})
        except OSError as e:
            print("Error: %s : %s" % (current_path, e.strerror))
            return Response(response = json.dumps({"msg": "Delete fail!", "status": 1}), status = 200, mimetype="application/json")
        return Response(response = json.dumps({"msg": "Delete data successfully!", "status": 0}), status = 200, mimetype="application/json")
    
    def __create_dir__(self, form):
        current_path = os.path.join(ROOT_PATH, form["path"])
        path = form['new_path']
        if os.path.exists(os.path.join(current_path, path)):
            return Response(response = json.dumps({'status': 2, 'msg': 'Dir already exists!'}), status = 200, mimetype="application/json")
        os.makedirs(os.path.join(current_path, path))
        return Response(response = json.dumps({'status': 0, 'msg': 'Create successfully!'}), status = 200, mimetype="application/json")

    
    def __delete_user__(self, form):
        current_path = os.path.join(ROOT_PATH, form["target_username"])
        try:
            if os.path.exists(current_path):
                shutil.rmtree(current_path)
            col.delete_one({'username': form["target_username"]})
            return Response(response = json.dumps({'status': 0, 'msg': 'Delete successfully!'}), status = 200, mimetype="application/json")
        except Exception as e:
            print(repr(e))
            return Response(response = json.dumps({'status': 1, 'msg': 'Delete fails!'}), status = 200, mimetype="application/json")
    
    def __confirm_user__(self, form):
        username = form['target_username']
        set_value = form['isValid']
        current_path = os.path.join(ROOT_PATH, form["target_username"])
        try:
            if not os.path.exists(current_path):
                os.mkdir(current_path)
            col.update_one({'username': username}, {"$set":{'isValid': set_value}})
            return Response(response = json.dumps({'status': 0, 'msg': 'Update successfully!'}), status = 200, mimetype="application/json")
        except Exception as e:
            print(repr(e))
            return Response(response = json.dumps({'status': 1, 'msg': 'Update fails!'}), status = 200, mimetype="application/json")
    
    def __update_admin__(self, form):
        username = form['target_username']
        set_value = form['isAdmin']
        try:
            col.update_one({'username': username}, {"$set":{'isAdmin': set_value}})
            return Response(response = json.dumps({'status': 0, 'msg': 'Update successfully!'}), status = 200, mimetype="application/json")
        except Exception as e:
            print(repr(e))
            return Response(response = json.dumps({'status': 1, 'msg': 'Update fails!'}), status = 200, mimetype="application/json")
    
    def __update_limit__(self, form):
        username = form['target_username']
        set_value = form['limit']
        try:
            col.update_one({'username': username}, {"$set":{'limit': set_value*1024*1024*1024}})
            return Response(response = json.dumps({'status': 0, 'msg': 'Update successfully!'}), status = 200, mimetype="application/json")
        except Exception as e:
            print(repr(e))
            return Response(response = json.dumps({'status': 1, 'msg': 'Update fails!'}), status = 200, mimetype="application/json")
    
    def __get_user__(self):
        doc = col.find()
        n_doc = []
        for item in doc:
            item.pop("_id")
            item["password"] = str(base64.b64decode(item["password"]), 'utf-8')
            n_doc.append(item)
        return Response(response = json.dumps({'status': 0, 'msg': 'Users got!', 'users': n_doc}), status = 200, mimetype="application/json")