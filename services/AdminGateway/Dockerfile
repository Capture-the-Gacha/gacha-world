FROM python:3.12-slim

WORKDIR /app

COPY *.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5001

CMD python app.py