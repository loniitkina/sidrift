# Variables
IMAGE_NAME=sidrift
CONTAINER_NAME=sidrift

# Targets
build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --name $(CONTAINER_NAME) -p 9000:9000 $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME)

clean:
	docker rm $(CONTAINER_NAME)
	docker rmi $(IMAGE_NAME)
