# Stage 1: Build Stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Set Python user base
ENV PYTHONUSERBASE=/root/.local

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tree \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime Stage
FROM python:3.11-slim

WORKDIR /app

# Set Python user base
ENV PYTHONUSERBASE=/root/.local
ENV PATH="/root/.local/bin:${PATH}"

# Install system dependencies required for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    tree \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# # Copy only the necessary files from the builder stage
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/bin/git /usr/bin/git
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /usr/bin/ssh-keygen /usr/bin/ssh-keygen
COPY --from=builder /usr/lib/ /usr/lib/

# SSH setup
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# Copy app files
COPY app/ .

# Set environment variables
ENV PATH="/root/.local/bin:${PATH}"

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--reload"]