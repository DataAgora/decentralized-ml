$(aws ecr get-login --region us-west-1 --no-include-email)
docker build -t cloud-image .
docker tag cloud-image 880058582700.dkr.ecr.us-west-1.amazonaws.com/cloud
docker push 880058582700.dkr.ecr.us-west-1.amazonaws.com/cloud