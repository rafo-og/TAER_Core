import yaml
from os import path


class Dict2Class:
    def __init__(self, my_dict: "dict[str, object]"):
        for key in my_dict:
            if type(my_dict[key]) is dict:
                setattr(self, key, Dict2Class(my_dict[key]))
            else:
                setattr(self, key, my_dict[key])


class Config:
    CONFIG_PATH = ""

    def __init__(self, config_path=None):
        if config_path is None:
            if path.exists(self.CONFIG_PATH):
                self.value = self.__load_config(self.CONFIG_PATH)
        else:
            if path.exists(config_path):
                self.value = self.__load_config(config_path)

    def __load_config(self, file_path: str):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)


class ViewConfig:
    def __init__(self):
        config = Config()
        Dict2Class.__init__(self, config.value["VIEW"])


class ModelConfig:
    def __init__(self):
        config = Config()
        Dict2Class.__init__(self, config.value["MODEL"])
