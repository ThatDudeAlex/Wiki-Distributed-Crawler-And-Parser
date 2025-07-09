from dynaconf import Dynaconf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
print('Config Loader Base Dir: %s', BASE_DIR)


def get_settings(component: str) -> Dynaconf:
    return Dynaconf(
        settings_files=[
            str(BASE_DIR / "config" / "global_config.yml"),
            str(BASE_DIR / "config" / f"{component}_config.yml"),
        ],
        environments=True,
        load_dotenv=True,
        envvar_prefix=False
    )
