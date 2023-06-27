# FileManagerBackEnd
The Flask backend of FileManager: https://github.com/hinczhang/FileManager
### RUN
```
sh ./run_docker.sh
```

### Response code requirement
- 0: Successful response  
- 1: Invalid operations  
- 2: Existence error  
- 3: Database error
### Configuration
The should be an file called `conf.ini` under the folder `/src/web/`, the format should be: 
```
[redis]
port = xxxx
localhost = xxxx
password = xxxx
[mongodb]
client = "mongodb://user:password@ip:port/"
user = xxxx
password = xxxx
url = xxxx
port= xxxx
[key]
token_key = xxxx
database_key = xxxx
```
### Upload volume control
```
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100MB
```
In `src/web/_init_.py`.  
Please change the value of `MAX_CONTENT_LENGTH` to control the maximum size of uploaded files.