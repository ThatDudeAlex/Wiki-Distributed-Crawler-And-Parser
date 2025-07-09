import docker
import uuid

from shared.configs.load_config import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
client = docker.from_env()


def build_component_image(component_name: str, dockerfile_name: str = "Dockerfile", tag: str = None):
    """
    Build a Docker image for a specific component

    :param component_name: e.g. "crawler"
    :param dockerfile_name: e.g. "Dockerfile" (default)
    :param tag: Optional tag (auto-generated if None)
    :return: (image_tag: str)
    """
    if tag is None:
        tag = f"{component_name}_test_{uuid.uuid4().hex[:8]}"

    dockerfile_path = Path("components") / component_name / dockerfile_name

    client.images.build(
        path=str(PROJECT_ROOT),
        dockerfile=str(dockerfile_path),
        tag=tag
    )

    return tag


def assert_file_exists(container, path):
    code, _ = container.exec_run(f"test -f {path}")
    assert code == 0, f"Expected file '{path}' not found"


def assert_dir_exists(container, path):
    code, _ = container.exec_run(f"test -d {path}")
    assert code == 0, f"Expected directory '{path}' not found"


def test_container_file_structure():
    # 1. Setup
    client = docker.from_env()
    tag = f"test_fs_{uuid.uuid4().hex[:8]}"
    tag = build_component_image('crawler')

    # 2. Act

    # Run the container
    container = client.containers.run(
        # The image being used (the component image)
        tag,

        # Runs in the background (doesn't block)
        detach=True,

        # The container name (makes it easier to inspect/cleanup)
        name=tag,

        # Gives it a pseudo terminal (allows running terminal commands)
        tty=True,

        # Override default CMD/entrypoint (Don't start main app)
        entrypoint="sleep",

        # Keep it alive (sleep for 60 seconds)
        command="60",

        # Automatically delete container when it exits
        remove=True,
    )

    # 3. Assert
    try:
        # Test that the container has requirement files
        assert_file_exists(container, 'requirements-common.txt')
        assert_file_exists(container, 'components/crawler/requirements.txt')

        # Test that the container has require shared directories
        assert_dir_exists(container, 'database')
        assert_dir_exists(container, 'shared')
    finally:
        try:
            container.kill()
        except Exception:
            pass  # Already exited or removed
