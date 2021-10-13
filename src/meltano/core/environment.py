"""Meltano runtime environments."""

import copy
from typing import Dict, List, Optional, Tuple

from meltano.core.behavior import NameEq
from meltano.core.behavior.canonical import Canonical
from meltano.core.plugin import PluginType
from meltano.core.plugin.base import PluginRef


class EnvironmentNotFound(Exception):
    """Exception raised when a Meltano environment was not found."""


class EnvironmentPluginConfig(PluginRef):
    """Environment configuration for a plugin."""

    def __init__(
        self,
        plugin_type: PluginType,
        name: str,
        config: Optional[dict] = None,
        **extras,
    ):
        """Create a new plugin configuration object.

        Args:
            plugin_type: Extractor, loader, etc.
            name: Name of the plugin.
            config: Plugin configuration.
            extras: Plugin extras.
        """
        super().__init__(plugin_type, name)
        self.config = copy.deepcopy(config or {})
        self.extras = extras

    @property
    def extra_config(self):
        """Get extra config from the Meltano environment, like `select` and `schema`."""
        return {f"_{key}": value for key, value in self.extras.items()}

    @property
    def config_with_extras(self):
        """Get plugin configuration values from the Meltano environment."""
        return {**self.config, **self.extra_config}


class EnvironmentConfig(Canonical):
    """Meltano environment configuration."""

    def __init__(self, plugins: Dict[str, List[dict]] = None):
        """Create a new environment configuration.

        Args:
            plugins: Mapping of plugin types to arrays of plugin configurations.
        """
        super().__init__()
        self.plugins = self.load_plugins(plugins or {})

    def load_plugins(
        self,
        plugins: Dict[str, List[dict]],
    ) -> Dict[Tuple[PluginType, str], EnvironmentPluginConfig]:
        """Create plugin configurations from raw dictionary.

        Args:
            plugins: Plugin configurations.

        Returns:
            A mapping of plugin type and name to configurations.
        """
        plugin_mapping = {}
        for raw_plugin_type, raw_plugins in plugins.items():
            plugin_type = PluginType(raw_plugin_type)
            for raw_plugin in raw_plugins:
                plugin = EnvironmentPluginConfig(plugin_type=plugin_type, **raw_plugin)
                plugin_mapping[(plugin_type, plugin.name)] = plugin

        return plugin_mapping


class Environment(NameEq, Canonical):
    """Runtime environment for Meltano runs."""

    def __init__(
        self,
        name: str,
        config: dict = None,
    ) -> None:
        """Create a new environment object.

        Args:
            name: Environment name. Must be unique. Defaults to None.
            config: Dictionary with environment configuration.
        """
        super().__init__()

        self.name = name
        self.config = EnvironmentConfig(**(config or {}))

    def get_plugin_config(
        self,
        plugin_type: PluginType,
        name: str,
    ) -> Optional[EnvironmentPluginConfig]:
        """Get configuration for a plugin in this environment.

        Args:
            plugin_type: Extractor, loader, etc.
            name: Plugin name.

        Returns:
            A plugin configuration object if one is present in this environment.
        """
        return self.config.plugins.get((plugin_type, name))
