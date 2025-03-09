FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chmod +x run.sh

EXPOSE 8000

CMD ["./run.sh"]
