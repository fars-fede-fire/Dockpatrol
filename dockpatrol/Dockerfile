FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc

RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update && apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LO https://github.com/getsops/sops/releases/download/v3.10.0/sops-v3.10.0.linux.amd64
RUN mv sops-v3.10.0.linux.amd64 /usr/local/bin/sops
RUN chmod +x /usr/local/bin/sops

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dockpatrol.py .

RUN mkdir -p stacks

ENV SOPS_AGE_KEY_FILE="/app/key.txt"

ENV GITHUB_OWNER=""
ENV GITHUB_REPO=""
ENV GITHUB_BRANCH="main"
ENV GITHUB_TOKEN=""
ENV GITHUB_STACKS_DIR="stacks" 
ENV INTERVAL="300"

CMD ["python", "dockpatrol.py"]
