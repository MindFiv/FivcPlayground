import os

from typing import Any, Optional


class SettingsConfig(object):
    def __init__(self, config_file: str = "settings.yaml"):
        self.config_file = os.path.abspath(os.path.join(os.getcwd(), config_file))
        self.errors = []
        self.configs = {}
        self.configs = self._load_file(self.config_file)
        if self.errors:
            print(f"Errors loading config: {self.errors}, in directory: {os.getcwd()}")

    def _load_yaml_file(self, filename: str):
        import yaml

        try:
            with open(filename, "r") as f:
                conf = yaml.safe_load(f)
                assert isinstance(conf, dict)
                return conf
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ) as e:
            self.errors.append(e)
            return {}

    def _load_json_file(self, filename: str):
        import json

        try:
            with open(filename, "r") as f:
                conf = json.load(f)
                assert isinstance(conf, dict)
                return conf
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            self.errors.append(e)
            return {}

    def _load_file(self, filename: str):
        ext = filename.split(".")[-1]
        if ext in ["yml", "yaml"]:
            return self._load_yaml_file(filename)
        elif ext == "json":
            return self._load_json_file(filename)
        else:
            self.errors.append(ValueError(f"Unsupported config file type: {ext}"))
            return {}

    def _save_yaml_file(self, filename: str):
        import yaml

        try:
            with open(filename, "w") as f:
                yaml.safe_dump(self.configs, f)
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ) as e:
            self.errors.append(e)

    def _save_json_file(self, filename: str):
        import json

        try:
            with open(filename, "w") as f:
                json.dump(self.configs, f)
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            self.errors.append(e)

    def _save_file(self, filename: str):
        ext = filename.split(".")[-1]
        if ext in ["yml", "yaml"]:
            self._save_yaml_file(filename)
        elif ext == "json":
            self._save_json_file(filename)
        else:
            self.errors.append(ValueError(f"Unsupported config file type: {ext}"))

    def get(self, key: str, default: Any = None) -> Any:
        return self.configs.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.configs[key] = value

    def save(self, filename: Optional[str] = None) -> None:
        if filename is None:
            filename = self.config_file
        self._save_file(filename)
