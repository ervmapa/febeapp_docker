Frontend-Backend-Redis Application

This application demonstrates the interaction between a frontend, backend, and Redis using Docker Compose. Follow the steps below to set up and use the application.

Prerequisites:

- Docker installed on your machine

build images with:
docker build -t frontend . --network=host
docker build -t backenend . --network=host


Getting Started:

1. Clone the repository:

    git clone https://github.com/your/repo.git
    cd repo

2. Start the frontend, backend, and Redis containers:

    docker-compose up

Usage:

After the containers are up and running, you can interact with the application using curl commands. The frontend will store user and data in Redis, then communicate with the backend.

Example Requests:

1. Create User and Data:

    curl -X POST -H "Content-Type: application/json" -d '{"type": "create", "user": "myuser", "data": "mydata"}' http://localhost:5000/control

    Example Response:

    {"message": "Backend request processed successfully"}

2. Delete User and Data:

    curl -X POST -H "Content-Type: application/json" -d '{"type": "delete", "user": "myuser", "data": "mydata"}' http://localhost:5000/control

    Example Response:

    {"message": "Backend request processed successfully"}

Notes:

- Ensure that the Docker containers are running (docker-compose up) before making requests.
- Replace "myuser" and "mydata" with your desired user and data values.

