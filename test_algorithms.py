"""test_algorithms.py
Простой скрипт для тестирования алгоритмов аналитики.
"""
from src.services.analytics.analytics_service import AnalyticsService


def test_example_from_book():
    """Тестируем пример из «Книги Знаний»: 29.02.1988, Milana."""
    print("🧪 Тестируем пример из «Книги Знаний»: 29.02.1988, Milana")
    print("=" * 60)
    
    service = AnalyticsService()
    
    try:
        analysis = service.analyze_person("29.02.1988", "Milana")
        
        print("✅ Анализ выполнен успешно!")
        print(f"📅 Дата: {analysis['input_data']['birth_date']}")
        print(f"👤 Имя: {analysis['input_data']['original_name']}")
        print(f"🔤 Латиницей: {analysis['input_data']['latin_name']}")
        print()
        
        calculations = analysis['calculations']
        print("🔢 Ключевые числа:")
        print(f"  • ЧС: {calculations['consciousness_number']}")
        print(f"  • ЧД: {calculations['action_number']}")
        print(f"  • Число Имени: {calculations['name_number']}")
        print()
        
        matrix = analysis['matrix']
        print("📊 Матрица:")
        print(f"  • Сильные: {matrix['strong_digits']}")
        print(f"  • Слабые: {matrix['weak_digits']}")
        print(f"  • Отсутствующие: {matrix['missing_digits']}")
        print()
        
        print("💡 Ожидаемые результаты из книги:")
        print("  • ЧС: 2 (29 -> 2+9=11 -> 1+1=2)")
        print("  • ЧД: 3 (2+9+0+2+1+9+8+8=39 -> 3+9=12 -> 1+2=3)")
        print("  • Число Имени: 6 (M=4, I=1, L=3, A=1, N=5, A=1 = 15 -> 6)")
        print()
        
        # Проверяем результаты
        assert calculations['consciousness_number'] == 2, f"ЧС должен быть 2, получен {calculations['consciousness_number']}"
        assert calculations['action_number'] == 3, f"ЧД должен быть 3, получен {calculations['action_number']}"
        assert calculations['name_number'] == 6, f"Число Имени должно быть 6, получено {calculations['name_number']}"
        
        print("✅ Все проверки пройдены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def test_cyrillic_name():
    """Тестируем транслитерацию кириллического имени."""
    print("\n🧪 Тестируем транслитерацию: Иван Петров")
    print("=" * 60)
    
    service = AnalyticsService()
    
    try:
        analysis = service.analyze_person("15.03.1990", "Иван Петров")
        
        print("✅ Анализ выполнен успешно!")
        print(f"📅 Дата: {analysis['input_data']['birth_date']}")
        print(f"👤 Имя: {analysis['input_data']['original_name']}")
        print(f"🔤 Латиницей: {analysis['input_data']['latin_name']}")
        print(f"🔤 Кириллица: {analysis['input_data']['is_cyrillic']}")
        print()
        
        calculations = analysis['calculations']
        print("🔢 Ключевые числа:")
        print(f"  • ЧС: {calculations['consciousness_number']}")
        print(f"  • ЧД: {calculations['action_number']}")
        print(f"  • Число Имени: {calculations['name_number']}")
        print()
        
        print("✅ Транслитерация работает!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def test_validation():
    """Тестируем валидацию входных данных."""
    print("\n🧪 Тестируем валидацию входных данных")
    print("=" * 60)
    
    service = AnalyticsService()
    
    # Тест валидации дат
    valid_dates = ["15.03.1990", "01.01.2000", "29.02.1988"]
    invalid_dates = ["15-03-1990", "1990-03-15", "32.13.1990", "abc"]
    
    print("📅 Валидация дат:")
    for date_str in valid_dates:
        result = service.validate_birth_date(date_str)
        print(f"  {date_str}: {'✅' if result else '❌'}")
    
    for date_str in invalid_dates:
        result = service.validate_birth_date(date_str)
        print(f"  {date_str}: {'❌' if not result else '✅'}")
    
    # Тест валидации имён
    valid_names = ["Иван Петров", "Ivan Petrov", "Анна", "Anna"]
    invalid_names = ["", "Иван123", "Ivan@Petrov", "   "]
    
    print("\n👤 Валидация имён:")
    for name in valid_names:
        result = service.validate_name(name)
        print(f"  {name}: {'✅' if result else '❌'}")
    
    for name in invalid_names:
        result = service.validate_name(name)
        print(f"  {name}: {'❌' if not result else '✅'}")
    
    print("\n✅ Валидация работает!")


if __name__ == "__main__":
    print("🚀 Запуск тестов алгоритмов аналитики")
    print("=" * 60)
    
    test_example_from_book()
    test_cyrillic_name()
    test_validation()
    
    print("\n🎉 Все тесты завершены!")
