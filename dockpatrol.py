import os
import subprocess
import time
import logging
import git
import docker

logging.basicConfig(level=logging.DEBUG)

docker_client = docker.from_env()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH')
GITHUB_STACKS_DIR = os.getenv('GITHUB_STACKS_DIR')
LOCAL_REPO_PATH=os.getenv('LOCAL_REPO_PATH')
INTERVAL = int(os.getenv('INTERVAL'))


def run_command(command, cwd=None, capture_output=False):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, text=True,
                                capture_output=capture_output)
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error running command: {command} - {e}")
        return None
    
def clone_or_update_repo():
    """Clone or update the entire GitHub repository, ensuring a clean state."""
    if os.path.exists(LOCAL_REPO_PATH) and os.path.isdir(os.path.join(LOCAL_REPO_PATH, ".git")):
        logging.info("📥 Cleaning and updating repository...")

        # Remove all untracked files and directories to ensure only Git-tracked files remain
        run_command("git fetch --all", cwd=LOCAL_REPO_PATH)
        run_command("git reset --hard origin/{GITHUB_BRANCH}", cwd=LOCAL_REPO_PATH)
        run_command("git clean -xdf", cwd=LOCAL_REPO_PATH)  # Deletes untracked files and directories
    else:
        logging.info(f"📦 Cloning full repository {GITHUB_OWNER}/{GITHUB_REPO} (branch: {GITHUB_BRANCH})...")

        # Remove any corrupted or incomplete repo directory
        if os.path.exists(LOCAL_REPO_PATH):
            run_command(f"rm -rf {LOCAL_REPO_PATH}")

        # Clone the full repository
        run_command(f"git clone -b {GITHUB_BRANCH} https://{GITHUB_TOKEN}@github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git {LOCAL_REPO_PATH}")

    logging.info("✅ Repository is up to date.")

   

def find_compose_files():
    """Find all docker-compose.yml or docker-compose.yaml files in the specified stacks directory."""
    compose_files = []
    stacks_path = os.path.join(LOCAL_REPO_PATH, GITHUB_STACKS_DIR)

    for root, _, files in os.walk(stacks_path):
        for filename in ["docker-compose.yml", "docker-compose.yaml"]:
            if filename in files:
                compose_files.append(os.path.join(root, filename))
    
    return compose_files

def start_containers():
    """Deploy containers using docker-compose, decrypting .env.enc files if necessary."""
    compose_files = find_compose_files()

    logging.debug(f"COMPOSE FILES: {compose_files}")

    for compose_file in compose_files:
        compose_dir = os.path.dirname(compose_file)
        env_enc_file = os.path.join(compose_dir, ".env.enc")
        env_file = os.path.join(compose_dir, ".env")

        if os.path.exists(env_enc_file):
            logging.info(f"🔐 Decrypting {env_enc_file}...")
            run_command(f"sops --decrypt --input-type dotenv --output-type dotenv --age /app/key.txt {env_enc_file} > {env_file}")

        env_option = f"--env-file {env_file}" if os.path.exists(env_file) else ""
        logging.debug(f"🚀 Starting services for: {compose_file}")

        run_command(f"docker compose up -d", cwd=compose_dir)


def list_expected_containers():
    """Get expected container names from docker-compose files."""
    expected_containers = set()
    compose_files = find_compose_files()
    
    for compose_file in compose_files:
        output = run_command(f"docker compose ps --services", cwd=os.path.dirname(compose_file), capture_output=True)
        expected_containers.update(output.splitlines())

    logging.debug(f"EXPEPCTED CONTAINERS: {expected_containers}")

    return expected_containers

def stop_unexpected_containers():
    """Stop and remove containers that are not part of the expected stack, unless labeled to be kept."""
    all_containers = docker_client.containers.list(all=True)
    expected_containers = list_expected_containers()
    logging.debug(f"ALL RUNNING CONTAINERS: {all_containers}")

    for container_id in all_containers:
        try:
            logging.debug(f"CONTAINER_ID: {container_id.name}")
            container = docker_client.containers.get(container_id.id)
            prune_label = container.labels.get("dockpatrol_prune", "").lower() if container.labels else ""

            if container_id.name in expected_containers:
                logging.info(f"⚠️ Skipping container {container.name} because it is a part of git")

            elif prune_label in ["false", "off", "0", "no"]:
                logging.info(f"⚠️ Skipping container {container.name} due to prune exclusion label (dockpatrol_prune={prune_label}).")
            else:
                logging.info(f"🛑 Removing unexpected container: {container.name}")
                run_command(f"docker stop {container.id}")

        except Exception as e:
            logging.error(f"Error processing container {container_id.id}: {e}")

def prune_old_images():
    """Remove unused images and stopped containers."""
    logging.debug("🧹 Pruning unused Docker resources...")
    run_command("docker system prune -f")

def run_sync():
    """Runs the full sync process once."""
    logging.info("🔄 Syncing repository and ensuring correct services are running...")
    clone_or_update_repo()
    start_containers()
    stop_unexpected_containers()
    prune_old_images()

def main():
    """Main function to run on an interval or once."""
    if INTERVAL == 0:
        logging.info("🛠 Running once and shutting down...")
        run_sync()
    else:
        while True:
            run_sync()
            logging.info(f"⏳ Waiting {INTERVAL} seconds before the next check...")
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
    
    
