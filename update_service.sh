docker system prune -f
cd cloud-node
chmod +x docker_helper.sh
./docker_helper.sh
cd ..
cd explora
chmod +x docker_helper.sh
./docker_helper.sh
cd ..
source api-env/bin/activate
cd dashboard-api
python update_service.py
zappa update dev
deactivate