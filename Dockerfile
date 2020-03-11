FROM python:3

WORKDIR /usr/src/app

COPY credentials.json ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./run.py"]
