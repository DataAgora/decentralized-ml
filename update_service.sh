cd cloud-node
chmod +x docker_helper.sh
./docker_helper.sh
cd ..
cd explora
chmod +x docker_helper.sh
./docker_helper.sh
cd ..
cd dashboard-api
python update_service.py