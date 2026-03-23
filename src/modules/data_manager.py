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

@dataclass
class GraphsData:
    """Класс-контейнер для хранения подготовленных списков для Matplotlib"""
    dates: List[str] = field(default_factory=list)
    expenses: List[float] = field(default_factory=list)
    income: List[float] = field(default_factory=list)
    common: List[float] = field(default_factory=list)

def prepare_graph_data() -> GraphsData:
    """Читает JSON и упаковывает данные в объект GraphsData"""
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
            
        # Считаем общий баланс (Доход + Расход) с помощью NumPy или обычным циклом
        res.common = (np.array(res.income) + np.array(res.expenses)).tolist()
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка чтения данных: {e}")
        
    return res

def save_json(amount: float, category: str, op_type: str):
    
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
            
