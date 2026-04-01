import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from src.modules.data_manager import FinanceManager

class GraphService:
    """Сервис для генерации фигур Matplotlib"""
    
    def __init__(self):
        # Загружаем данные один раз при создании сервиса
        self.data = FinanceManager().prepare_graph_data()
        
    def build_all(self) -> Figure:
        """Создает комплексный график: Доходы, Расходы и Баланс"""
        fig = plt.figure() # Создаем НОВУЮ фигуру (чтобы не было наложений)
    
        # Рисуем три линии разными цветами
        plt.plot(self.data.dates, self.data.expenses, label="Расход", c="#AE0505", marker='o')
        plt.plot(self.data.dates, self.data.income, label="Доход", c="#008e18", marker='s')
        plt.plot(self.data.dates, self.data.common, label="Баланс", c="#cbc51a", linestyle='--')
        
        plt.xticks(rotation=45) # Наклоняем даты для читаемости
        plt.title("Общая аналитика")
        plt.legend()
        plt.grid(True)
        plt.tight_layout() # Подгоняем размеры, чтобы ничего не вылезло за края
        return fig

    def build_expenses(self) -> Figure:
        """График только расходов"""
        fig = plt.figure()
        plt.fill_between(self.data.dates, self.data.expenses, color="#AE0505", alpha=0.3)
        plt.plot(self.data.dates, self.data.expenses, c="#AE0505", label="Расход")
        plt.xticks(rotation=45 )
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        return fig
    
    def build_income(self) -> Figure:
        """График только доходов"""
        fig = plt.figure()
        plt.fill_between(self.data.dates, self.data.income, color = "#0de711", alpha=0.3)
        plt.plot(self.data.dates, self.data.income, label="Доход", c="#0de711")
        plt.xticks(rotation = 45)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        return fig
