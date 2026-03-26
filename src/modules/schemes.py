from pathlib import Path  # Работа с файловыми путями и расположением
from typing import List, Dict  # Типы для аннотаций
from pydantic import BaseModel, Field, field_validator, ConfigDict  # Для построения схемы и валидации данных

# Указываем путь к корневой директории проекта и JSON-файлу с данными
ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / 'data' / 'finance_data.json'


class Transaction(BaseModel):
    """Модель одной финансовой операции (транзакции)."""
    
    model_config = ConfigDict(populate_by_name=True)
    operation: str = Field(alias='операция')
    category: str = Field(min_length=2, alias='категория')
    amount: float = Field( alias='сумма')

    # Валидатор для поля operation: проверяет, что значение - "доход" или "расход"
    @field_validator('operation')
    @classmethod
    def check_op_type(cls, v: str) -> str:
        """Проверяем корректность типа операции (доход/расход)."""
        
        normalized = v.lower().strip()
        if normalized not in ('доход', 'расход'):
            raise ValueError('Тип операции должен быть "доход" или "расход"')
        return normalized


class DayData(BaseModel):
    """Модель данных для одного дня."""
    model_config = ConfigDict(populate_by_name=True)
    total_income: float = Field(default=0.0, alias='общий доход')
    total_expenses: float = Field(default=0.0, alias='общий расход')
    elements: List[Transaction] = Field(default_factory=list, alias='элементы')


class FinanceStorage(BaseModel):
    """Хранилище всех данных по датам."""

    days: Dict[str, DayData] = Field(default_factory=dict) # Словарь: ключ - дата (строка), значение - объект DayData
