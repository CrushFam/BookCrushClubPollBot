FROM python:3.8-slim-buster
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN git clone https://mpr.makedeb.org/just && cd just && makedeb -si

COPY . .

CMD just setup
CMD just run
