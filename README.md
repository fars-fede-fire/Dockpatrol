# Dockpatrol

### One container to rule them all!

Dockpatrol is an automated GitOps tool that keeps your Docker environment clean and up-to-date by syncing Docker stacks from a GitHub repository, decrypting secrets, deploying services via docker-compose, and removing any unexpected containers.

## Features

- Clone or update a GitHub repository
- Automatically detect and deploy docker-compose files
- Decrypt environment secrets using Mozilla SOPS (.env.enc)
- Remove containers not defined in the repository
- Skip specific containers with a label
- Run periodically or once

## Prebuilt Docker Image

You can use the prebuilt Docker image directly from your container registry:

```bash
docker pull <your-registry>/<your-image>:<tag>
```

## Quick Start

Run the container with your environment variables and volume mounts:

```bash
docker run --rm \
  -e GITHUB_TOKEN=ghp_... \
  -e GITHUB_OWNER=youruser \
  -e GITHUB_REPO=yourrepo \
  -e GITHUB_BRANCH=main \
  -e GITHUB_STACKS_DIR=stacks \
  -e LOCAL_REPO_PATH=/app/stacks \
  -e INTERVAL=300 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/key.txt:/app/key.txt \
  <your-registry>/<your-image>:<tag>
```

Set `INTERVAL=0` to run the sync once and exit.

## Docker-compose.yaml example

```bash
services:
  dockpatrol:
    container_name: dockpatrol
    image: dockpatrol:latest
    volumes:
      - ./key.txt:/app/key.txt
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    environment:
      - GITHUB_OWNER=${GITHUB_OWNER}
      - GITHUB_REPO=${GITHUB_REPO}
      - GITHUB_BRANCH=${GITHUB_BRANCH}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_STACKS_DIR=${GITHUB_STACKS_DIR} 
      - LOCAL_REPO_PATH=${LOCAL_REPO_PATH}
      - INTERVAL=${INTERVAL}
    labels:
      - dockpatrol_prune=false
    

```

## Secrets with SOPS

If your repository includes encrypted `.env.enc` files, Dockpatrol will decrypt them using a mounted age key. Example:

```bash
-v $(pwd)/key.txt:/app/key.txt
```

## Prune Logic

Dockpatrol will:

- Start containers defined in your GitHub repo's compose files
- Stop and remove any container not listed
- Skip containers with this label:

```yaml
labels:
  - "Dockpatrol_prune=false"
```

- Clean up unused images and containers with `docker system prune -f`

## Example Repository Layout

```
your-repo/
└── stacks/
    ├── service-a/
    │   ├── docker-compose.yml
    │   └── .env.enc
    └── service-b/
        └── docker-compose.yaml
```

## Environment Variables

| Variable            | Description                                                |
|---------------------|------------------------------------------------------------|
| GITHUB_TOKEN        | GitHub token with repo access                              |
| GITHUB_OWNER        | GitHub user or org name                                    |
| GITHUB_REPO         | Repository name                                            |
| GITHUB_BRANCH       | Branch to sync (e.g. main)                                 |
| GITHUB_STACKS_DIR   | Path to stacks directory inside repo                       |
| LOCAL_REPO_PATH     | Local clone path (inside the container)                   |
| INTERVAL            | Sync interval in seconds (use 0 to run once and exit)      |
| SOPS_AGE_KEY_FILE   | Path to age decryption key (default: `/app/key.txt`)       |

## License

MIT License. Free to use, modify, and contribute.