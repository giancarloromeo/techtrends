FROM python:3.8

LABEL maintainer="Giancarlo Romeo <giancarloromeo@gmail.com>"

ADD techtrends /app

WORKDIR /app

RUN pip install -r requirements.txt && python init_db.py

EXPOSE 3111

CMD [ "python", "app.py" ]
