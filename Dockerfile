FROM python:3.8

LABEL Zhang, Jiongyan hinczhang@whu.edu.cn

WORKDIR /home/hinczhang/
COPY requirements.txt /home/hinczhang/
RUN pip install -r requirements.txt
COPY ./src /home/hinczhang/

CMD [ "python", "/home/hinczhang/run.py" ]


 