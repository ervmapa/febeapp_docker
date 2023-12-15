# Use an official Alpine Linux as a parent image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose a port for your Flask application to listen on
EXPOSE 5001

# Define environment variables
ENV REDIS_HOST=redishost

# Define the command to run your application
CMD ["python", "backend.py"]

