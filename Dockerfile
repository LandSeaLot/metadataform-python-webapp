FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["streamlit", "run", "main.py"]