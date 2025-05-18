# Set base image
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tree \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# SSH setup
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# Install Python dependencies
COPY . .

RUN git clone git@github.com:Mennatalla-Khougha/roadmap-tasks.git

RUN cp firebase_key.json roadmap-tasks/

RUN cd roadmap-tasks/

WORKDIR /app/roadmap-tasks

RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--reload"]