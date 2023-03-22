# Use the official Python image as the base image
FROM mambaorg/micromamba:1.3.1
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes
USER root

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .
COPY setup.py  .

# Copy the rest of the application code to the working directory
COPY . .


# activate python env
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# Install the dependencies
# RUN pip install -r requirements.txt
RUN pip install -e .

# Expose the port that the application will run on
EXPOSE 9000

# Start the application with uvicorn
CMD ["python3", "/app/bin/webapp", "--host", "0.0.0.0", "--port", "8000"]
