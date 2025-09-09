#!/usr/bin/env python3
"""Скрипт для запуска тестов."""
import subprocess
import sys
import os


def run_command(command, description):
    """Запускает команду и выводит результат."""
    print(f"\n{'='*50}")
    print(f"🚀 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    """Основная функция."""
    print("🧪 Запуск тестов для Telegram Bot")
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("src"):
        print("❌ Запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    # Устанавливаем зависимости для тестов
    if not run_command("pip install -r requirements-test.txt", "Установка зависимостей для тестов"):
        print("❌ Не удалось установить зависимости")
        sys.exit(1)
    
    # Запускаем unit тесты
    if not run_command("python -m pytest tests/unit/ -v", "Запуск unit тестов"):
        print("❌ Unit тесты не прошли")
        sys.exit(1)
    
    # Запускаем тесты с покрытием
    if not run_command("python -m pytest tests/ --cov=src --cov-report=html", "Запуск тестов с покрытием"):
        print("❌ Тесты с покрытием не прошли")
        sys.exit(1)
    
    print("\n✅ Все тесты прошли успешно!")
    print("📊 Отчет о покрытии создан в htmlcov/index.html")


if __name__ == "__main__":
    main()
