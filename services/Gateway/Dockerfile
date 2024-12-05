FROM python:3.12-slim

WORKDIR /app

COPY ./services/Gateway/*.py .
COPY ./services/Gateway/requirements.txt .
COPY ./services/Player/model.py player_model.py
COPY ./services/Auth/model.py auth_model.py
COPY ./services/Auction/model.py auction_model.py

# Useless, just to avoid errors
COPY ./services/Player/connection.py connection.py

RUN pip install -r requirements.txt

EXPOSE 5000

CMD python app.py