FROM python:3.6
COPY * /app/
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8888
EXPOSE 80
ADD script.sh /
RUN chmod +x /script.sh
CMD ["/script.sh"]
