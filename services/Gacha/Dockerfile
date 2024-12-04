FROM python:3.12-slim

WORKDIR /app

COPY *.py .
COPY requirements.txt .

RUN python -m pip install -r requirements.txt

EXPOSE 5000

CMD python app.py