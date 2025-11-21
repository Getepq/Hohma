FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ДОБАВЛЕНО: Создаём директорию /data
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
