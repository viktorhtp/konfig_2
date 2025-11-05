import xml.etree.ElementTree as ET
import sys
import os
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List


class ConfigError(Exception):
    pass


class DependencyFetchError(Exception):
    pass


class DependencyVisualizer:
    def __init__(self):
        self.config = {}
        self.dependencies = []

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

    def fetch_dependencies(self) -> List[str]:
        """Получение прямых зависимостей пакета из PyPI JSON API"""
        package_name = self.config['package_name']

        print(f"Получение зависимостей для пакета '{package_name}'...")

        if self.config['test_mode'] == 'true':
            return self._fetch_from_test_file()
        else:
            return self._fetch_from_pypi(package_name)

    def _fetch_from_pypi(self, package_name: str) -> List[str]:
        """Получение зависимостей из PyPI JSON API"""
        try:
            # Используем PyPI JSON API вместо Simple API
            api_url = f"https://pypi.org/pypi/{package_name}/json"

            # Загружаем JSON данные о пакете
            with urllib.request.urlopen(api_url) as response:
                data = json.loads(response.read().decode('utf-8'))

            # Извлекаем зависимости из информации о пакете
            dependencies = self._extract_dependencies_from_json(data)
            self.dependencies = dependencies
            return dependencies

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise DependencyFetchError(f"Пакет '{package_name}' не найден в PyPI")
            else:
                raise DependencyFetchError(f"HTTP ошибка: {e.code}")
        except urllib.error.URLError as e:
            raise DependencyFetchError(f"Ошибка подключения: {e.reason}")
        except json.JSONDecodeError as e:
            raise DependencyFetchError(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            raise DependencyFetchError(f"Ошибка получения зависимостей: {e}")

    def _extract_dependencies_from_json(self, data: Dict) -> List[str]:
        """Извлечение зависимостей из JSON данных PyPI"""
        dependencies = []

        # Ищем зависимости в информации о пакете
        info = data.get('info', {})

        # Зависимости могут быть в requires_dist
        requires_dist = info.get('requires_dist', [])
        if requires_dist:
            for requirement in requires_dist:
                # Извлекаем имя пакета из строки требования
                # Формат: "package-name [optional] (version)"
                package_match = requirement.split(' ')[0]
                if package_match and not package_match.startswith('['):
                    dependencies.append(package_match)

        # Если не нашли в requires_dist, пробуем requires
        if not dependencies:
            requires = info.get('requires', [])
            if requires:
                dependencies.extend(requires)

        # Убираем дубликаты и возвращаем
        return list(set(dependencies))

    def _fetch_from_test_file(self) -> List[str]:
        """Получение зависимостей из тестового файла"""
        test_file_path = self.config['test_repository_path']

        if not os.path.exists(test_file_path):
            raise DependencyFetchError(f"Тестовый файл '{test_file_path}' не найден")

        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            package_name = self.config['package_name']
            self.dependencies = self._parse_dependencies_from_file(content, package_name)
            return self.dependencies

        except Exception as e:
            raise DependencyFetchError(f"Ошибка чтения тестового файла: {e}")

    def _parse_dependencies_from_file(self, content: str, package_name: str) -> List[str]:
        """Парсинг зависимостей из тестового файла"""
        lines = content.strip().split('\n')

        for line in lines:
            if ':' in line:
                pkg_name, deps_str = line.split(':', 1)
                if pkg_name.strip().lower() == package_name.lower():
                    dependencies = [dep.strip() for dep in deps_str.split(',') if dep.strip()]
                    return dependencies

        raise DependencyFetchError(f"Пакет '{package_name}' не найден в тестовом файле")

    def print_config(self) -> None:
        print("Конфигурация приложения:")
        print("-" * 40)
        for key, value in self.config.items():
            print(f"{key:25}: {value}")
        print("-" * 40)

    def print_dependencies(self) -> None:
        """Вывод прямых зависимостей пакета (требование этапа 2)"""
        if not self.dependencies:
            print(f"Пакет '{self.config['package_name']}' не имеет прямых зависимостей")
            return

        print(f"Прямые зависимости пакета '{self.config['package_name']}':")
        print("-" * 40)
        for i, dep in enumerate(self.dependencies, 1):
            print(f"{i:2}. {dep}")
        print("-" * 40)


def main():
    try:
        visualizer = DependencyVisualizer()
        config = visualizer.load_config()
        visualizer.print_config()

        # Получение и вывод зависимостей (этап 2)
        dependencies = visualizer.fetch_dependencies()
        visualizer.print_dependencies()

        print(f"\nЭтап 2 завершен успешно!")
        print(f"Найдено зависимостей: {len(dependencies)}")

    except (ConfigError, DependencyFetchError) as e:
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