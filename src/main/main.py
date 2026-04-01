import sys
from pathlib import Path

# Находим путь к корню проекта (на две папки выше от main.py)
ROOT_PATH = Path(__file__).resolve().parent.parent.parent
# Собираем путь к картинке
BG_SOURCE = str(ROOT_PATH / 'assets' / 'bg.png')
sys.path.insert(0,str(ROOT_PATH)) # Добавили корневую папку в "список поиска"


from datetime import date # noqa
from kivy.app import App # noqa
from kivy.lang import Builder # noqa
from kivy.properties import ObjectProperty, StringProperty # noqa
from kivy.uix.floatlayout import FloatLayout # noqa
from kivy.uix.popup import Popup # noqa
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg # noqa

# Подключаем наши модули
from src.modules.data_manager import FILE # noqa
from src.modules.graphs import GraphService # noqa
from src.modules.data_manager import prepare_graph_data, FinanceManager # noqa


class AddPopup(Popup):
    """Окно добавления новой операции"""
    amount_input = ObjectProperty(None)
    category_input = ObjectProperty(None)
    caller = ObjectProperty(None) # Ссылка на MainScreen для обновления истории
    op_type = StringProperty("")  # "доход" или "расход"

    def save(self):
        """Валидация, сохранение в JSON и закрытие окна"""
        try:
            val = float(self.amount_input.text)
            cat = self.category_input.text.strip()
            if not cat: 
                return
        except ValueError:
            print("Ошибка: сумма должна быть числом!")
            return
        try:
            # загружаю add_transaction из основного MyApp(App) с помощью  App.get_running_app() 
            # FinanceManager загружен в MyApp под атрибутом self.management 
            App.get_running_app().management.add_transaction(val, cat, self.op_type)    
            
            # Просим главный экран обновить список последних записей
            if self.caller:
                self.caller.update_history()
        except Exception as e:
            print(f"ошибка{e}")
            
        self.dismiss() # Закрываем попап
            
        

class GraphPopup(Popup):
    """Окно с Accordion для отображения графиков"""
    pass

class MainScreen(FloatLayout):
    """Главный экран приложения"""
    
    # свойство, которое будет хранить путь к фону
    bg_path = StringProperty(BG_SOURCE)
    
    def open_popup(self, operation_type: str):
        """Открывает окно ввода с предзаданным типом операции"""
        p = AddPopup(op_type=operation_type, caller=self)
        p.title = f"Добавить {operation_type}"
        p.open()

    def update_history(self):
        """Умный сбор последних 5 записей из JSON для отображения на экране"""
      
        manager = App.get_running_app().management
        count = 0
        lines = ["Последние операции:"]
        
        # идем по датам с конца (reversed)
        for d in reversed(manager.storage.days.keys()):
            # Идем по элементам внутри дня с конца
            day = manager.storage.days[d] # Достаем объект дня
            f_d = date.fromisoformat(d).strftime("%d-%m-%Y")  # Форматируем дату из ISO (2026-03-17) в RU (17-03)
            for item in reversed(day.elements):  #  Берем список транзакций одного дня
                lines.append(f"{f_d} | {item.operation}: {item.category} - {item.amount}р")
                count += 1
                if count >= 5: 
                    break
            if count >= 5: 
                break
        
        self.ids.last_entry.text = "\n".join(lines)

    def show_statistics(self,button):
        
        balance = App.get_running_app().management
        data = prepare_graph_data()
        if button == "доход":
            self.ids.sum_stat.text =f"{sum(data.income)}"
        elif button == "Баланс":
            self.ids.sum_stat.text = f"{balance.get_total_balance()}"
        else:
            self.ids.sum_stat.text =f"{sum(data.expenses)}"

    def show_graphs(self):
        """Генерирует графики и вставляет их в GraphPopup"""
        p = GraphPopup()
        service = GraphService() # Инициализируем сбор данных
        
        # Вклеиваем холст Matplotlib в BoxLayout попапа
        p.ids.all_graphs.add_widget(FigureCanvasKivyAgg(service.build_all()))
        p.ids.ex_graphs.add_widget(FigureCanvasKivyAgg(service.build_expenses()))
        p.ids.in_graphs.add_widget(FigureCanvasKivyAgg(service.build_income()))
        p.open()

class MyApp(App):
    def build(self):
        # загружаем FinanceManager в основной класс kivy для дальнейшего использования через  get_running_app()
        self.management = FinanceManager()  
        # Подгружаем дизайн из ui.kv
        Builder.load_file('ui.kv')
        return MainScreen() 

if __name__ == '__main__':
    # Обязательно создаем папку data, если её нет
    Path('data').mkdir(exist_ok=True)
    MyApp().run()
