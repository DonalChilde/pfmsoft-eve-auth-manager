"""Configuration models and OAuth-related constants for Eve Auth Manager."""

from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_DNS, uuid5

from pydantic_settings import BaseSettings, SettingsConfigDict
from typer import get_app_dir

from pfmsoft.eve_auth_manager import (
    __app_name__,
    __url__,
    __version__,
)

# Typical application settings
USER_AGENT = f"{__app_name__}/{__version__} ({__url__})"
"""User-Agent header value sent to remote OAuth and ESI services."""
APP_DOMAIN = f"{__app_name__}"
APP_NAMESPACE = uuid5(NAMESPACE_DNS, __app_name__)
ENV_PREFIX = __app_name__.replace(".", "_").replace("-", "_").upper() + "_"
SETTINGS_KEY = ENV_PREFIX + "SETTINGS"

# OAuth-related constants
AUDIENCE = "EVE Online"
"""Expected JWT audience for EVE SSO access tokens."""
OAUTH_METADATA_URL = (
    "https://login.eveonline.com/.well-known/oauth-authorization-server"
)
"""URL to fetch OAuth metadata from the ESI auth server."""


@dataclass(slots=True, kw_only=True)
class EveAuthManagerSettings:
    """Normalized runtime settings used by the application."""

    application_directory: Path
    authorization_database_path: Path
    logging_directory: Path


class EveAuthManagerSettingsPydantic(BaseSettings):
    """Settings for the application loaded from environment variables and optional `.env` files.

    Values are read from environment variables prefixed with the application name,
    altered to uppercase and with non-alphanumeric characters replaced by underscores.
    Values are also read from `.env` or `.env.dev` when present.
    """

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file=(".env", ".env.dev"),
        env_file_encoding="utf-8",
    )
    application_directory: Path = Path(get_app_dir(__app_name__)).resolve()


def get_settings(
    application_directory: Path | None = None,
) -> EveAuthManagerSettings:
    """Build runtime settings from a Pydantic settings model or application directory.

    Args:
        application_directory (Path | None): Optional application directory path.
            If not provided, the default application directory is used.

    Returns:
        Runtime settings dataclass used by the application.

    Raises:
        ValueError: If the provided application directory exists but is not a directory.
    """
    if application_directory is None:
        # If the application directory is not provided, use the value from the Pydantic
        # settings model. This allows for environment variable overrides and .env file loading.
        application_directory = EveAuthManagerSettingsPydantic().application_directory
    application_directory = application_directory.expanduser().resolve()
    if application_directory.exists() and not application_directory.is_dir():
        raise ValueError(
            f"Application directory '{application_directory}' exists but is not a directory."
        )
    settings = _initialize_settings(application_directory)
    return settings


def _initialize_settings(application_directory: Path) -> EveAuthManagerSettings:
    """Build default runtime settings.

    Also ensures that the application directories exist.
    """
    settings = EveAuthManagerSettings(
        application_directory=application_directory,
        authorization_database_path=application_directory / "eve_auth_manager.sqlite",
        logging_directory=application_directory / "logs",
    )
    # Ensure that the application directories exist.
    settings.application_directory.mkdir(parents=True, exist_ok=True)
    settings.logging_directory.mkdir(parents=True, exist_ok=True)
    return settings
