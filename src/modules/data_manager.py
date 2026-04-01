import json
import numpy as np
from pathlib import Path
from datetime import date
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Находим корень проекта относительно самого файла data_manager.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Теперь собираем путь к базе данных
FILE = BASE_DIR / 'data' / 'finance_data.json'
# На всякий случай создаем папку data, если её нет (автоматизация!)
FILE.parent.mkdir(parents=True, exist_ok=True)

from src.modules.schemes import FinanceStorage, DayData, Transaction # noqa

@dataclass
class GraphsData:
    """Класс-контейнер для хранения подготовленных списков для Matplotlib"""
    dates: List[str] = field(default_factory=list)
    expenses: List[float] = field(default_factory=list)
    income: List[float] = field(default_factory=list)
    common: List[float] = field(default_factory=list)

def prepare_graph_data() -> GraphsData:
    """Читает JSON и упаковывает данные в объект GraphsData для построения графиков."""
    if not FILE.exists():
        return GraphsData()
        
    res = GraphsData()
    try:
        with open(FILE, 'r', encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)
            
        # Итерируемся по датам (ключам словаря)
        for d_str in data.keys():
            # Форматируем дату из ISO (2026-03-17) в RU (17-03)
            format_date = date.fromisoformat(d_str).strftime("%d-%m-%Y")
            res.dates.append(format_date)
            
            # Достаем агрегированные суммы (если ключа нет, берем 0)
            res.expenses.append(float(data[d_str].get("общий расход", 0)))
            res.income.append(float(data[d_str].get("общий доход", 0)))
            
        # Считаем общий баланс (Доход + Расход) с помощью NumPy
        res.common = (np.array(res.income) + np.array(res.expenses)).tolist()
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка чтения данных: {e}")
        
    return res

def save_json(amount: float, category: str, op_type: str):
    """Сохраняет транзакцию в JSON файл."""
    
    today = date.today().isoformat()
            
    # Читаем существующий JSON или создаем новый
    data = json.load(open(FILE, 'r', encoding='utf-8')) if FILE.exists() else {}
    
    # Инициализируем структуру дня, если её еще нет
    day = data.setdefault(today, {"общий доход": 0, "общий расход": 0, "элементы": []})
    
    # Добавляем запись в список "элементы"
    day["элементы"].append({
        "операция": op_type,
        "категория": category,
        "сумма": amount
    })
    
    # Обновляем агрегированные суммы дня
    if op_type == "доход":
        day["общий доход"] += amount
    else:
        day["общий расход"] += amount * (-1)
    
    # Записываем обновленный словарь обратно в файл
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
            
class FinanceManager():
    """Класс для управления финансовыми данными, включая загрузку, добавление транзакций и сохранение."""
    def __init__(self):
        # Инициализируем хранилище, загружая данные из файла
        self.storage = self.load_storage()

    # Метод для загрузки данных из файла
    def load_storage(self) -> Dict[str, DayData]:
        """Загружает данные из JSON файла и возвращает объект FinanceStorage.
        Returns:
            {} Объект с загруженными данными или пустой, если файл не существует.
        """
        
        if not FILE.exists():  # Если файл не существует
            return FinanceStorage()  # Возвращаем пустое хранилище
        try:
            with open(FILE, 'r', encoding='utf-8') as f:   # Открываем файл для чтения
                raw_data = json.load(f)  # Загружаем JSON  raw_data = dict вида {дата: DayData}

            return FinanceStorage(days=raw_data)  # Оборачиваем словарь в Pydantic-модель

        except Exception as e:
            print(f"Ошибка загрузки базы: {e}")
            return FinanceStorage()
    # Метод для добавления транзакции
    def add_transaction(self, amount: float, category: str, op_type: str):
        """Добавляет новую транзакцию за сегодняшний день.
        
        Args:
            amount: Сумма транзакции (положительная).
            category: Категория транзакции.
            op_type: Тип операции ("доход" или "расход").
        """
        today = date.today().isoformat()  # Получаем сегодняшнюю дату в формате ISO YYYY-MM-DD 
        
        # Если дня нет, создаем новый DayData
        if today not in self.storage.days:
            self.storage.days[today] = DayData()
        
        # Получаем или создаём данные за сегодня
        day = self.storage.days[today]  
        
        # Создаём новую транзакцию
        new_trans = Transaction(operation=op_type, 
                                category=category, 
                                amount=amount)
        
        day.elements.append(new_trans)  # Добавляем в список операций дня
        
        # Обновляем статистику
        if op_type == "доход":  # Если доход
            day.total_income += amount  # Увеличиваем доход
        else:  # Если расход
            day.total_expenses += -amount   # Увеличиваем расход (с минусом?)
            
        # Сохраняем изменения в файл
        self.save_file()

    def save_file(self):
        """Сохраняет текущие данные в JSON файл."""
        # Превращаем все объекты DayData обратно в словари для JSON
        data_to_save = {
            dt: day.model_dump(by_alias=True, exclude_none=True) 
            for dt, day in self.storage.days.items()
        }
        with open(FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
    
    def get_total_balance(self) -> float:
        """Вычисляет общий баланс по всем дням.
        Returns:
            float: Сумма доходов и расходов по всем дням.
        """
        daily_balance = []
        # Проходим по всем дням
        for i in self.storage.values():
            # Баланс = доход + расход (если расход хранится как отрицательный)
            daily_balance.append(sum([i.total_income,i.total_expenses]))
        return sum(daily_balance)
    
    def prepare_graph_data(self):
        """Читает JSON и упаковывает данные в объект GraphsData"""
        
        res = GraphsData()  # создаем переменную используя контейнер GraphsData 
        lst_dates = sorted(self.storage.days.keys()) # собираем список дат
        
        for item in lst_dates:
            data = self.storage.days[item] # берем дату 
            format_date = date.fromisoformat(item).strftime("%d-%m-%Y") # форматируем дату под привычный формат
            # закидываем данные в соответствующие контейнеры  
            res.dates.append(format_date) 
            res.expenses.append(data.total_expenses)
            res.income.append(data.total_income)
            res.common.append(data.total_income + data.total_expenses)
        return res
