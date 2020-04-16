FROM python:3.6
COPY . /app/
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip uninstall -y notebook
RUN pip install notebook
EXPOSE 8888
EXPOSE 80
ADD script.sh /
RUN chmod +x /script.sh
WORKDIR /app/notebooks
CMD ["/script.sh"]
