import argparse
import subprocess
import sys
import yaml
from pathlib import Path

BASE_COMPOSE = Path("docker/docker-compose.yml")
ENV_COMPOSE_DIR = Path("docker/environments")
MONITORING_COMPOSE = Path("docker/monitoring/docker-compose.monitoring.yml")
SCALING_CONFIG_DIR = Path("docker/environments/deploy_configs")


def run_command(cmd: list[str]):
    """Runs a shell command and exits if it fails."""
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"❌ Command failed: {' '.join(cmd)}")
        sys.exit(result.returncode)


def load_scaling_config(env: str) -> dict:
    path = SCALING_CONFIG_DIR / f"scaling.{env}.yml"
    if not path.exists():
        print(f"❌ Scaling config not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        return yaml.safe_load(f)
    

def build_service(compose_files: list[Path], service: str):
    cmd = ["docker", "compose"]
    for f in compose_files:
        cmd += ["-f", str(f)]
    cmd += ["build", "--no-cache", service]
    run_command(cmd)


def up_service(compose_files: list[Path], service: str, scale_count: int) -> bool:
    if scale_count <= 0:
        print(f"Skipping {service} (scale set to 0)")
        return False

    cmd = ["docker", "compose"]
    for f in compose_files:
        cmd.extend(["-f", str(f)])

    cmd.extend(["up", "-d", "--remove-orphans"])
    if scale_count > 1:
        cmd.extend(["--scale", f"{service}={scale_count}"])
    cmd.append(service)

    run_command(cmd)
    return True

    
def build_and_up(compose_files: list[Path], service: str, scale_count: int, build=False):
    if scale_count <= 0:
        print(f"Skipping {service} (scale set to 0)")
        return

    if build:
        build_service(compose_files, service)

    up_service(compose_files, service, scale_count)


def deploy_component_gradually(components: dict, compose_files: list[Path], service):
    target_scale = components.get(service, {}).get("scaling", 0)

    # Handle 1 instance as a special case
    if target_scale == 1:
        build_and_up(compose_files, service, target_scale, build=True)
        return

    build_service(compose_files, service)

    print(f"Gradually Scaling {service} (2 → {target_scale})...")

    current_scale = 0
    while current_scale < target_scale:
        next_scale = current_scale + 2

        # If target is odd, just jump to the target
        if next_scale > target_scale:
            next_scale = target_scale

        current_scale = next_scale
        print(f"Scaling {service} to {current_scale}...")
        up_service(compose_files, service, current_scale)

        if current_scale < target_scale:
            run_command(["sleep", "2"])

    print(f"✅ {service} scaled to {target_scale}")



def deploy_monitoring_services(compose_files: list[Path]):
    print("📊 Deploying monitoring stack (Prometheus, Grafana, PgAdmin, Node Exporter, cAdvisor)...")

    services = [
        "prometheus",
        "grafana",
        "pgadmin",
        "node-exporter",
        "cadvisor"
    ]

    # Build all monitoring & deploy all monitoring services
    for service in services:
        build_and_up(compose_files, service, 1, True)

    print("✅ Monitoring services deployed.")


def main():
    parser = argparse.ArgumentParser(description="Deploy the distributed crawler system.")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev", help="Environment to deploy")
    parser.add_argument("--monitoring", action="store_true", help="Include monitoring stack")
    args = parser.parse_args()

    # Compose file list
    compose_files = [
        BASE_COMPOSE,
        ENV_COMPOSE_DIR / f"docker-compose.{args.env}.yml"
    ]
    if args.monitoring:
        compose_files.append(MONITORING_COMPOSE)
        deploy_monitoring_services(compose_files)

    scaling = load_scaling_config(args.env)
    components = scaling.get("components", {})

    docker_context = f"distribute-{args.env}"
    run_command(['docker', 'context', 'use', docker_context])

    print(f"Deploying to {args.env.upper()} environment")

    # Step 1: Infra
    build_and_up(compose_files, "rabbitmq", 1, build=True)
    build_and_up(compose_files, "postgres", 1, build=True)
    build_and_up(compose_files, "postgres_initiator", 1, build=True)
    build_and_up(compose_files, "redis", 1, build=True)
    print("Infrastructured Deployed Successfully...")
    run_command(["sleep", "2"])

    # Step 2: Deploy DB components
    for service in ["db_reader", "db_writer"]:
        scale = components.get(service, {}).get("scaling", 0)
        build_and_up(compose_files, service, scale, build=True)
        run_command(["sleep", "2"])
    
    # Step 3: Deploy scheduler
    deploy_component_gradually(components, compose_files, 'scheduler')

    # Step 4: Deploy parser
    deploy_component_gradually(components, compose_files, 'parser')


    # Step 5: Deploy crawler(s)
    crawler_cfg = components.get("crawler", {})
    use_proxies = crawler_cfg.get("use_proxies", False)

    # Always deploy crawler_noproxy if defined
    if "crawler_noproxy" in crawler_cfg:
        scale = crawler_cfg["crawler_noproxy"].get("scaling", 0)
        build_and_up(compose_files, "crawler_noproxy", scale, build=True)
        run_command(["sleep", "2"])

    # Deploy proxy crawlers only if enabled
    if use_proxies:
        proxies = crawler_cfg.get("proxies", {})
        for service, settings in proxies.items():
            scale = settings.get("scaling", 0)
            if up_service(compose_files, service, scale):
                run_command(["sleep", "2"])

    # Step 5: Deploy dispatcher & rescheduler
    for service in ["dispatcher", "rescheduler"]:
        scale = components.get(service, {}).get("scaling", 0)
        build_and_up(compose_files, service, scale, build=True)
        run_command(["sleep", "2"])

    print("🎉 Deployment completed successfully!")


if __name__ == "__main__":
    main()
