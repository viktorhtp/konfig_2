import xml.etree.ElementTree as ET
import sys
import os
from typing import Dict, Any


class ConfigError(Exception):
    pass


class DependencyVisualizer:
    def __init__(self):
        self.config = {}

    def load_config(self, config_path: str = 'config.xml') -> Dict[str, Any]:
        if not os.path.exists(config_path):
            raise ConfigError(f"Файл '{config_path}' не найден")
        if not os.access(config_path, os.R_OK):
            raise ConfigError(f"Нет прав на чтение файла '{config_path}'")

        try:
            tree = ET.parse(config_path)
            root = tree.getroot()

            self.config = {
                'package_name': self._get_element_text(root, 'package_name'),
                'repository_url': self._get_element_text(root, 'repository_url'),
                'test_mode': self._get_element_text(root, 'test_mode', 'false'),
                'test_repository_path': self._get_element_text(root, 'test_repository_path'),
                'output_filename': self._get_element_text(root, 'output_filename')
            }

            self._validate_config()
            return self.config

        except ET.ParseError as e:
            raise ConfigError(f"Ошибка парсинга XML: {e}")
        except Exception as e:
            raise ConfigError(f"Ошибка загрузки конфигурации: {e}")

    def _get_element_text(self, root, element_name: str, default: str = None) -> str:
        element = root.find(element_name)
        if element is None or element.text is None:
            if default is not None:
                return default
            raise ConfigError(f"Параметр '{element_name}' отсутствует или пуст")
        return element.text.strip()

    def _validate_config(self) -> None:
        if not self.config['package_name']:
            raise ConfigError("Имя пакета не может быть пустым")

        test_mode = self.config['test_mode'].lower()
        if test_mode not in ('true', 'false'):
            raise ConfigError("Режим тестирования должен быть 'true' или 'false'")
        self.config['test_mode'] = test_mode

        if test_mode == 'true':
            if not self.config['test_repository_path']:
                raise ConfigError("Путь к тестовому репозиторию обязателен")
        else:
            url = self.config['repository_url']
            if not url or not (url.startswith('http://') or url.startswith('https://')):
                raise ConfigError("URL репозитория обязателен и должен начинаться с http:// или https://")

        if not self.config['output_filename']:
            raise ConfigError("Имя выходного файла не может быть пустым")

    def print_config(self) -> None:
        print("Конфигурация приложения:")
        print("-" * 40)
        for key, value in self.config.items():
            print(f"{key:25}: {value}")
        print("-" * 40)


def main():
    try:
        visualizer = DependencyVisualizer()
        config = visualizer.load_config()
        visualizer.print_config()

        print(f"\nПриложение настроено!")
        print(f"Пакет: {config['package_name']}")
        print(f"Режим: {'тестовый' if config['test_mode'] == 'true' else 'продуктовый'}")

    except ConfigError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПрервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()