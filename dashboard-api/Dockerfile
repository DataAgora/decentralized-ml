FROM python:3.6
COPY cloud-node/* /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8999
CMD ["python", "server.py"]
