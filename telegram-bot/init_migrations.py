"""init_migrations.py
Скрипт для инициализации миграций Alembic.
"""
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> None:
    """Выполнить команду и показать результат."""
    print(f"🔧 Выполняю: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)


def main():
    """Инициализировать миграции."""
    print("🚀 Инициализация миграций Alembic...")
    
    # Проверяем, что мы в правильной директории
    if not Path("alembic.ini").exists():
        print("❌ Файл alembic.ini не найден. Запустите скрипт из корня проекта.")
        sys.exit(1)
    
    # Инициализируем миграции
    run_command(["alembic", "init", "migrations"])
    
    print("✅ Миграции инициализированы!")
    print("\n📝 Следующие шаги:")
    print("1. Создайте первую миграцию: alembic revision --autogenerate -m 'Initial migration'")
    print("2. Примените миграцию: alembic upgrade head")


if __name__ == "__main__":
    main()
