FROM python:3.11-slim
MAINTAINER Andrey "andrey@example.com"

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["python"]
CMD ["app.py"]