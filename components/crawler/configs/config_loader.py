from dynaconf import Dynaconf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

settings = Dynaconf(
    settings_files=[
        str(BASE_DIR / "config" / "global_config.yml"),
        str(BASE_DIR / "config" / "crawler_config.yml"),
    ],
    environments=True,
    load_dotenv=True
)
