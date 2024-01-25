FROM python:3.8-slim-buster
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN apt install snapd && snap install just

COPY . .

CMD just setup
CMD just run
