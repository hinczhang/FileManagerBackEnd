#!/bin/bash
docker rm -f filemanagerback_release
docker rmi filemanagerback:run
docker build -t filemanagerback:run .
docker run -itd -p 5001:5001 -v /home/hinczhang/fileDB:/home/hinczhang/fileDB --name filemanagerback_release filemanagerback:run /bin/bash
