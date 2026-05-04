FROM python:3.11-slim

WORKDIR /app

COPY app.py .

RUN pip install flask flask-cors boto3

EXPOSE 80

CMD ["python", "app.py"]
