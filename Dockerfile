FROM tensorflow/tensorflow:1.14.0-py3
COPY requirements.txt /
COPY train.py /
WORKDIR /
RUN pip3 install -r requirements.txt
