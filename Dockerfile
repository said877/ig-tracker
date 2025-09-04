FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget unzip curl chromium chromium-driver

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "instagram_tracker.py"]
