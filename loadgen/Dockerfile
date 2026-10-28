FROM python:3.12-slim

WORKDIR /srv/loadgen
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY loadgen.py .

CMD ["python", "loadgen.py"]
