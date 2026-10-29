from app_functions import (
    calc_discount, pluralize_items, format_full_name, 
    get_client_tier, get_client_loyalty_days
)
from datetime import datetime, timedelta

def run_tests():
    # Тесты для calc_discount
    assert calc_discount(1000, 20) == 800.0
    assert calc_discount(1000, None) == 0.0
    assert calc_discount(None, 10) == 0.0
    assert calc_discount(1000, 150) == 0.0  # скидка > 100
    assert calc_discount(1000, -10) == 1000.0 # скидка < 0
    assert calc_discount("1000", "10") == 900.0 # работа со строками
    
    # Тесты для pluralize_items
    assert pluralize_items(1) == "1 товар"
    assert pluralize_items(2) == "2 товара"
    assert pluralize_items(5) == "5 товаров"
    assert pluralize_items(21) == "21 товар"
    assert pluralize_items(22) == "22 товара"
    assert pluralize_items(25) == "25 товаров"
    assert pluralize_items(111) == "111 товаров"
    assert pluralize_items(0) == "0 товаров"
    assert pluralize_items(None) == "0 товаров"
    
    # Тесты для format_full_name
    assert format_full_name("иванов", "иван", "иванович") == "Иванов И.И."
    assert format_full_name(" петрова ", " анна ", None) == "Петрова А."
    assert format_full_name(None, "петр", "сергеевич") == "Аноним"
    assert format_full_name("сидоров", "", "павлович") == "Аноним"
    assert format_full_name("  волков  ", "  олег  ", "  львович  ") == "Волков О.Л."
    
    # Тесты для get_client_tier
    assert get_client_tier(0) == "Новичок"
    assert get_client_tier(4999) == "Новичок"
    assert get_client_tier(5000) == "Бронза"
    assert get_client_tier(19999) == "Бронза"
    assert get_client_tier(20000) == "Серебро"
    assert get_client_tier(49999) == "Серебро"
    assert get_client_tier(50000) == "Золото"
    assert get_client_tier(99999) == "Золото"
    assert get_client_tier(100000) == "Платина"
    assert get_client_tier(150000) == "Платина"
    assert get_client_tier(None) == "Без статуса"
    assert get_client_tier(-100) == "Без статуса"
    
    # Тесты для get_client_loyalty_days
    past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    assert get_client_loyalty_days(past_date) == 10
    assert get_client_loyalty_days(None) == 0
    assert get_client_loyalty_days("invalid-date") == 0

    print("Все тесты пройдены успешно.")

if __name__ == "__main__":
    run_tests()