FROM python:3.12-slim

WORKDIR /app

COPY cloud-training/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cloud-training/train.py .

CMD ["python", "train.py"]