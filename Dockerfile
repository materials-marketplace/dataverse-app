FROM python:3.9

RUN apt-get update
RUN pip install --upgrade pip

WORKDIR /app

ENV FLASK_APP=app.py
ENV PORT=8080

ADD . .
RUN pip install .

CMD flask run --host=0.0.0.0  --port=${PORT}

# docker-compose up -d
