"""
Инструмент визуализации графа зависимостей пакетов
Этап 1: Минимальный прототип с конфигурацией
"""

import xml.etree.ElementTree as ET
import sys
import os
from typing import Dict, Any


class ConfigError(Exception):
    """Исключение для ошибок конфигурации"""
    pass


class DependencyVisualizer:
    def __init__(self):
        self.config = {}
        self.default_config = {
            'package_name': 'requests',
            'repository_url': 'https://pypi.org/simple/',
            'test_mode': 'false',
            'test_repository_path': 'test_repo.txt',
            'output_filename': 'dependencies_graph.png'
        }

    def load_config(self, config_path: str = 'config.xml') -> Dict[str, Any]:
        """
        Загрузка конфигурации из XML файла

        Args:
            config_path: Путь к конфигурационному файлу

        Returns:
            Dict[str, Any]: Словарь с параметрами конфигурации

        Raises:
            ConfigError: При ошибках загрузки или валидации конфигурации
        """
        try:
            # Проверка существования файла
            if not os.path.exists(config_path):
                raise ConfigError(f"Конфигурационный файл '{config_path}' не найден")

            # Проверка прав доступа
            if not os.access(config_path, os.R_OK):
                raise ConfigError(f"Нет прав на чтение файла '{config_path}'")

            # Парсинг XML
            tree = ET.parse(config_path)
            root = tree.getroot()

            # Извлечение параметров с обработкой ошибок
            self.config['package_name'] = self._get_element_text(root, 'package_name')
            self.config['repository_url'] = self._get_element_text(root, 'repository_url')
            self.config['test_mode'] = self._get_element_text(root, 'test_mode', 'false')
            self.config['test_repository_path'] = self._get_element_text(root, 'test_repository_path')
            self.config['output_filename'] = self._get_element_text(root, 'output_filename')

            # Валидация параметров
            self._validate_config()

            return self.config

        except ET.ParseError as e:
            raise ConfigError(f"Ошибка парсинга XML файла: {e}")
        except Exception as e:
            raise ConfigError(f"Ошибка загрузки конфигурации: {e}")

    def _get_element_text(self, root, element_name: str, default: str = None) -> str:
        """
        Получение текста элемента с обработкой ошибок

        Args:
            root: Корневой элемент XML
            element_name: Имя элемента
            default: Значение по умолчанию (если элемент не найден)

        Returns:
            str: Текст элемента

        Raises:
            ConfigError: Если элемент обязательный и не найден
        """
        element = root.find(element_name)

        if element is None:
            if default is not None:
                return default
            raise ConfigError(f"Обязательный параметр '{element_name}' отсутствует в конфигурации")

        if element.text is None:
            if default is not None:
                return default
            raise ConfigError(f"Параметр '{element_name}' не может быть пустым")

        return element.text.strip()

    def _validate_config(self) -> None:
        """
        Валидация параметров конфигурации

        Raises:
            ConfigError: При невалидных значениях параметров
        """
        # Валидация имени пакета
        if not self.config['package_name']:
            raise ConfigError("Имя пакета не может быть пустым")

        if not isinstance(self.config['package_name'], str):
            raise ConfigError("Имя пакета должно быть строкой")

        # Валидация режима тестирования
        test_mode = self.config['test_mode'].lower()
        if test_mode not in ('true', 'false'):
            raise ConfigError("Режим тестирования должен быть 'true' или 'false'")

        self.config['test_mode'] = test_mode

        # Валидация в зависимости от режима
        if self.config['test_mode'] == 'true':
            # В режиме тестирования проверяем путь к тестовому репозиторию
            test_path = self.config['test_repository_path']
            if not test_path:
                raise ConfigError("Путь к тестовому репозиторию обязателен в режиме тестирования")

            # Проверяем расширение файла (опционально)
            if not test_path.endswith('.txt'):
                print(f"Предупреждение: тестовый репозиторий '{test_path}' рекомендуется сохранять в .txt формате",
                      file=sys.stderr)
        else:
            # В обычном режиме проверяем URL репозитория
            url = self.config['repository_url']
            if not url:
                raise ConfigError("URL репозитория обязателен в обычном режиме")

            if not isinstance(url, str):
                raise ConfigError("URL репозитория должен быть строкой")

            # Базовая валидация URL
            if not (url.startswith('http://') or url.startswith('https://')):
                raise ConfigError("URL репозитория должен начинаться с http:// или https://")

        # Валидация имени выходного файла
        output_file = self.config['output_filename']
        if not output_file:
            raise ConfigError("Имя выходного файла не может быть пустым")

        if not isinstance(output_file, str):
            raise ConfigError("Имя выходного файла должно быть строкой")

        # Проверяем расширение файла
        valid_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.pdf')
        if not any(output_file.lower().endswith(ext) for ext in valid_extensions):
            print(f"Предупреждение: выходной файл '{output_file}' имеет нестандартное расширение",
                  file=sys.stderr)

    def print_config(self) -> None:
        """Вывод конфигурации в формате ключ-значение"""
        print("=" * 50)
        print("Конфигурация приложения:")
        print("=" * 50)

        for key, value in self.config.items():
            print(f"{key:25}: {value}")

        print("=" * 50)


def demonstrate_error_handling():
    """
    Демонстрация обработки ошибок для различных сценариев
    """
    test_cases = [
        # (file_content, expected_error)
        ("nonexistent.xml", "Конфигурационный файл 'nonexistent.xml' не найден"),
    ]

    print("\nДемонстрация обработки ошибок:")
    print("-" * 40)

    visualizer = DependencyVisualizer()

    # Тест 1: Несуществующий файл
    try:
        visualizer.load_config("nonexistent.xml")
    except ConfigError as e:
        print(f"✓ Тест 1 (несуществующий файл): {e}")

    # Тест 2: Некорректный XML
    try:
        with open("bad_xml.xml", "w") as f:
            f.write("<config><package_name>test</config>")  # Незакрытый тег
        visualizer.load_config("bad_xml.xml")
    except ConfigError as e:
        print(f"✓ Тест 2 (некорректный XML): {e}")
    finally:
        if os.path.exists("bad_xml.xml"):
            os.remove("bad_xml.xml")

    # Тест 3: Отсутствие обязательного параметра
    try:
        with open("missing_param.xml", "w") as f:
            f.write("""<?xml version="1.0"?>
<config>
    <repository_url>https://test.com</repository_url>
    <test_mode>false</test_mode>
    <test_repository_path>test.txt</test_repository_path>
    <output_filename>graph.png</output_filename>
</config>""")  # Отсутствует package_name
        visualizer.load_config("missing_param.xml")
    except ConfigError as e:
        print(f"✓ Тест 3 (отсутствует package_name): {e}")
    finally:
        if os.path.exists("missing_param.xml"):
            os.remove("missing_param.xml")

    # Тест 4: Невалидный режим тестирования
    try:
        with open("invalid_mode.xml", "w") as f:
            f.write("""<?xml version="1.0"?>
<config>
    <package_name>test</package_name>
    <repository_url>https://test.com</repository_url>
    <test_mode>invalid</test_mode>
    <test_repository_path>test.txt</test_repository_path>
    <output_filename>graph.png</output_filename>
</config>""")
        visualizer.load_config("invalid_mode.xml")
    except ConfigError as e:
        print(f"✓ Тест 4 (невалидный test_mode): {e}")
    finally:
        if os.path.exists("invalid_mode.xml"):
            os.remove("invalid_mode.xml")

    print("-" * 40)


def main():
    """
    Основная функция приложения
    """
    try:
        # Создание и настройка визуализатора
        visualizer = DependencyVisualizer()

        # Загрузка конфигурации
        config = visualizer.load_config()

        # Вывод конфигурации (требование этапа 1)
        visualizer.print_config()

        # Демонстрация обработки ошибок
        demonstrate_error_handling()

        print(f"\nПриложение успешно настроено!")
        print(f"Будет анализироваться пакет: {config['package_name']}")
        print(f"Режим работы: {'тестовый' if config['test_mode'] == 'true' else 'продуктовый'}")

    except ConfigError as e:
        print(f"Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nПриложение прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()