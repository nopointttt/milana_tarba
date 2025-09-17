import webbrowser
import os
import time

# Получаем абсолютный путь к HTML файлу
html_file = os.path.abspath("Term_Sheet_Contract.html")
file_url = f"file:///{html_file.replace(os.sep, '/')}"

print(f"Открываю файл: {file_url}")
print("После открытия браузера:")
print("1. Нажмите Ctrl+P для печати")
print("2. Выберите 'Сохранить как PDF' в качестве принтера")
print("3. Сохраните файл как 'Соглашение_AI_ассистент.pdf'")

# Открываем файл в браузере по умолчанию
webbrowser.open(file_url)

print("\nФайл открыт в браузере. Выполните печать в PDF.")
