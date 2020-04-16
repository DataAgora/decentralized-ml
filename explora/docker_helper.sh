$(aws ecr get-login --region us-west-1 --no-include-email)
docker build -t explora-image .
docker tag explora-image 880058582700.dkr.ecr.us-west-1.amazonaws.com/explora
docker push 880058582700.dkr.ecr.us-west-1.amazonaws.com/explora