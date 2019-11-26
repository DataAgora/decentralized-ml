FROM python:3.6
COPY . /app
WORKDIR /app

# This is a weird fix for the dependencies. Be careful when modifying.
RUN pip install --no-cache-dir -r requirements.txt
# RUN pip uninstall tensorflow tensorflow-estimator tensorflow-hub tensorflowjs numpy Keras Keras-Applications Keras-Preprocessing -y
# RUN pip install 'tensorflow==1.13.1' 'keras==2.2.4'
# RUN pip install 'tensorflowjs==1.0.1'
# RUN pip uninstall numpy -y
# RUN pip install 'numpy==1.16.3'

EXPOSE 8999
CMD ["python", "cloud-node/server.py"]
