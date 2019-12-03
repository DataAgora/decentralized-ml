FROM python:3.6
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r cloud-node/requirements.txt
EXPOSE 8999
CMD ["python", "cloud-node/server.py"]
