import json
import csv
import os
from datetime import datetime
import operator
import re


# Утилиты для работы с датами
def get_current_timestamp():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def parse_date(date_str, with_time=False):
    try:
        if with_time:
            return datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
        else:
            return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return None
        

# Модель Заметки
class Note:
    def __init__(self, id, title, content, timestamp=None):
        self.id = id
        self.title = title
        self.content = content
        self.timestamp = timestamp if timestamp else get_current_timestamp()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        return Note(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            timestamp=data["timestamp"]
        )


# Менеджер Заметок
class NoteManager:
    def __init__(self, filepath='notes.json'):
        self.filepath = filepath
        self.notes = []
        self.load_notes()

    def load_notes(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                    self.notes = [Note.from_dict(note) for note in notes_data]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки заметок: {e}")
                self.notes = []
        else:
            self.notes = []

    def save_notes(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump([note.to_dict() for note in self.notes], f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Ошибка сохранения заметок: {e}")

    def create_note(self, title, content):
        try:
            if not title.strip():
                raise ValueError("Заголовок заметки не может быть пустым.")
            new_id = max([note.id for note in self.notes], default=0) + 1
            new_note = Note(id=new_id, title=title, content=content)
            self.notes.append(new_note)
            self.save_notes()
            print("Заметка успешно создана.")
        except ValueError as ve:
            print(f"Ошибка: {ve}")

    def list_notes(self):
        if not self.notes:
            print("Заметок нет.")
            return
        print("\nСписок заметок:")
        for note in self.notes:
            print(f"ID: {note.id}, Заголовок: {note.title}, Дата: {note.timestamp}")

    def view_note_details(self, note_id):
        note = self.get_note_by_id(note_id)
        if note:
            print(f"\nID: {note.id}")
            print(f"Заголовок: {note.title}")
            print(f"Содержимое: {note.content}")
            print(f"Дата изменения: {note.timestamp}")
        else:
            print("Заметка не найдена.")

    def edit_note(self, note_id, new_title, new_content):
        note = self.get_note_by_id(note_id)
        if note:
            try:
                if not new_title.strip():
                    raise ValueError("Заголовок заметки не может быть пустым.")
                note.title = new_title
                note.content = new_content
                note.timestamp = get_current_timestamp()
                self.save_notes()
                print("Заметка успешно обновлена.")
            except ValueError as ve:
                print(f"Ошибка: {ve}")
        else:
            print("Заметка не найдена.")

    def delete_note(self, note_id):
        note = self.get_note_by_id(note_id)
        if note:
            self.notes.remove(note)
            self.save_notes()
            print("Заметка успешно удалена.")
        else:
            print("Заметка не найдена.")

    def get_note_by_id(self, note_id):
        for note in self.notes:
            if note.id == note_id:
                return note
        return None

    def import_notes_csv(self, csv_filepath):
        try:
            with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    title = row.get('title', '').strip()
                    content = row.get('content', '').strip()
                    timestamp = row.get('timestamp', get_current_timestamp()).strip()
                    if not title:
                        print("Пропуск записи без заголовка.")
                        continue
                    new_id = max([note.id for note in self.notes], default=0) + 1
                    new_note = Note(id=new_id, title=title, content=content, timestamp=timestamp)
                    self.notes.append(new_note)
            self.save_notes()
            print("Импорт заметок завершен успешно.")
        except (IOError, csv.Error) as e:
            print(f"Ошибка импорта заметок: {e}")

    def export_notes_csv(self, csv_filepath):
        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'title', 'content', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for note in self.notes:
                    writer.writerow(note.to_dict())
            print("Экспорт заметок завершен успешно.")
        except IOError as e:
            print(f"Ошибка экспорта заметок: {e}")


# Модель Задачи
class Task:
    def __init__(self, id, title, description, done=False, priority='Средний', due_date=None):
        self.id = id
        self.title = title
        self.description = description
        self.done = done
        self.priority = priority
        self.due_date = due_date

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "done": self.done,
            "priority": self.priority,
            "due_date": self.due_date
        }

    @staticmethod
    def from_dict(data):
        return Task(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            done=data.get("done", False),
            priority=data.get("priority", "Средний"),
            due_date=data.get("due_date")
        )


# Менеджер Задач
class TaskManager:
    PRIORITIES = ['Высокий', 'Средний', 'Низкий']

    def __init__(self, filepath='tasks.json'):
        self.filepath = filepath
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    self.tasks = [Task.from_dict(task) for task in tasks_data]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки задач: {e}")
                self.tasks = []
        else:
            self.tasks = []

    def save_tasks(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump([task.to_dict() for task in self.tasks], f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Ошибка сохранения задач: {e}")

    def add_task(self, title, description, priority, due_date):
        try:
            if not title.strip():
                raise ValueError("Заголовок задачи не может быть пустым.")
            if priority not in self.PRIORITIES:
                raise ValueError(f"Приоритет должен быть одним из: {', '.join(self.PRIORITIES)}.")
            if due_date and not parse_date(due_date):
                raise ValueError("Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
            new_id = max([task.id for task in self.tasks], default=0) + 1
            new_task = Task(id=new_id, title=title, description=description,
                            priority=priority, due_date=due_date)
            self.tasks.append(new_task)
            self.save_tasks()
            print("Задача успешно добавлена.")
        except ValueError as ve:
            print(f"Ошибка: {ve}")

    def list_tasks(self, filter_by=None):
        filtered_tasks = self.tasks
        if filter_by:
            key, value = filter_by
            if key == 'status':
                filtered_tasks = [task for task in self.tasks if task.done == value]
            elif key == 'priority':
                filtered_tasks = [task for task in self.tasks if task.priority == value]
            elif key == 'due_date':
                filtered_tasks = [task for task in self.tasks if task.due_date == value]
        if not filtered_tasks:
            print("Задач нет.")
            return
        print("\nСписок задач:")
        for task in filtered_tasks:
            status = "Выполнено" if task.done else "В процессе"
            print(
                f"ID: {task.id}, Заголовок: {task.title}, Статус: {status}, Приоритет: {task.priority},"
                f" Срок: {task.due_date}")

    def mark_task_done(self, task_id):
        task = self.get_task_by_id(task_id)
        if task:
            task.done = True
            self.save_tasks()
            print("Задача отмечена как выполненная.")
        else:
            print("Задача не найдена.")

    def edit_task(self, task_id, title, description, priority, due_date):
        task = self.get_task_by_id(task_id)
        if task:
            try:
                if not title.strip():
                    raise ValueError("Заголовок задачи не может быть пустым.")
                if priority not in self.PRIORITIES:
                    raise ValueError(f"Приоритет должен быть одним из: {', '.join(self.PRIORITIES)}.")
                if due_date and not parse_date(due_date):
                    raise ValueError("Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
                task.title = title
                task.description = description
                task.priority = priority
                task.due_date = due_date
                self.save_tasks()
                print("Задача успешно обновлена.")
            except ValueError as ve:
                print(f"Ошибка: {ve}")
        else:
            print("Задача не найдена.")

    def delete_task(self, task_id):
        task = self.get_task_by_id(task_id)
        if task:
            self.tasks.remove(task)
            self.save_tasks()
            print("Задача успешно удалена.")
        else:
            print("Задача не найдена.")

    def get_task_by_id(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def import_tasks_csv(self, csv_filepath):
        try:
            with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    title = row.get('title', '').strip()
                    description = row.get('description', '').strip()
                    priority = row.get('priority', 'Средний').strip()
                    due_date = row.get('due_date', '').strip()
                    done = row.get('done', 'False').strip().lower() == 'true'
                    if not title:
                        print("Пропуск задачи без заголовка.")
                        continue
                    if priority not in self.PRIORITIES:
                        priority = 'Средний'
                    if due_date and not parse_date(due_date):
                        due_date = None
                    new_id = max([task.id for task in self.tasks], default=0) + 1
                    new_task = Task(id=new_id, title=title, description=description,
                                    priority=priority, due_date=due_date)
                    new_task.done = done
                    self.tasks.append(new_task)
            self.save_tasks()
            print("Импорт задач завершен успешно.")
        except (IOError, csv.Error) as e:
            print(f"Ошибка импорта задач: {e}")

    def export_tasks_csv(self, csv_filepath):
        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'title', 'description', 'done', 'priority', 'due_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for task in self.tasks:
                    writer.writerow(task.to_dict())
            print("Экспорт задач завершен успешно.")
        except IOError as e:
            print(f"Ошибка экспорта задач: {e}")

    def filter_tasks(self, key, value):
        if key == 'status':
            done = True if value.lower() in ['выполнено', 'done', 'true', '1'] else False
            self.list_tasks(filter_by=('status', done))
        elif key == 'priority':
            if value not in self.PRIORITIES:
                print(f"Неверный приоритет. Доступные: {', '.join(self.PRIORITIES)}.")
                return
            self.list_tasks(filter_by=('priority', value))
        elif key == 'due_date':
            if not parse_date(value):
                print("Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
                return
            self.list_tasks(filter_by=('due_date', value))
        else:
            print("Неверный критерий фильтрации.")


# Модель Контакта
class Contact:
    def __init__(self, id, name, phone, email):
        self.id = id
        self.name = name
        self.phone = phone
        self.email = email

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email
        }

    @staticmethod
    def from_dict(data):
        return Contact(
            id=data["id"],
            name=data["name"],
            phone=data["phone"],
            email=data["email"]
        )


# Менеджер Контактов
class ContactManager:
    def __init__(self, filepath='contacts.json'):
        self.filepath = filepath
        self.contacts = []
        self.load_contacts()

    def load_contacts(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    contacts_data = json.load(f)
                    self.contacts = [Contact.from_dict(contact) for contact in contacts_data]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки контактов: {e}")
                self.contacts = []
        else:
            self.contacts = []

    def save_contacts(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump([contact.to_dict() for contact in self.contacts], f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Ошибка сохранения контактов: {e}")

    def add_contact(self, name, phone, email):
        try:
            if not name.strip():
                raise ValueError("Имя контакта не может быть пустым.")
            if phone and not phone.isdigit():
                raise ValueError("Номер телефона должен содержать только цифры.")
            if email and "@" not in email:
                raise ValueError("Неверный формат электронной почты.")
            new_id = max([contact.id for contact in self.contacts], default=0) + 1
            new_contact = Contact(id=new_id, name=name, phone=phone, email=email)
            self.contacts.append(new_contact)
            self.save_contacts()
            print("Контакт успешно добавлен.")
        except ValueError as ve:
            print(f"Ошибка: {ve}")

    def search_contacts(self, keyword):
        results = [contact for contact in self.contacts if
                   keyword.lower() in contact.name.lower() or keyword in contact.phone]
        if not results:
            print("Контакты не найдены.")
            return
        print("\nРезультаты поиска:")
        for contact in results:
            print(f"ID: {contact.id}, Имя: {contact.name}, Телефон: {contact.phone}, Email: {contact.email}")

    def edit_contact(self, contact_id, name, phone, email):
        contact = self.get_contact_by_id(contact_id)
        if contact:
            try:
                if not name.strip():
                    raise ValueError("Имя контакта не может быть пустым.")
                if phone and not phone.isdigit():
                    raise ValueError("Номер телефона должен содержать только цифры.")
                if email and "@" not in email:
                    raise ValueError("Неверный формат электронной почты.")
                contact.name = name
                contact.phone = phone
                contact.email = email
                self.save_contacts()
                print("Контакт успешно обновлен.")
            except ValueError as ve:
                print(f"Ошибка: {ve}")
        else:
            print("Контакт не найден.")

    def delete_contact(self, contact_id):
        contact = self.get_contact_by_id(contact_id)
        if contact:
            self.contacts.remove(contact)
            self.save_contacts()
            print("Контакт успешно удален.")
        else:
            print("Контакт не найден.")

    def get_contact_by_id(self, contact_id):
        for contact in self.contacts:
            if contact.id == contact_id:
                return contact
        return None

    def import_contacts_csv(self, csv_filepath):
        try:
            with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    name = row.get('name', '').strip()
                    phone = row.get('phone', '').strip()
                    email = row.get('email', '').strip()
                    if not name:
                        print("Пропуск контакта без имени.")
                        continue
                    if phone and not phone.isdigit():
                        print(f"Пропуск контакта с неверным телефоном: {phone}")
                        continue
                    if email and "@" not in email:
                        print(f"Пропуск контакта с неверным email: {email}")
                        continue
                    new_id = max([contact.id for contact in self.contacts], default=0) + 1
                    new_contact = Contact(id=new_id, name=name, phone=phone, email=email)
                    self.contacts.append(new_contact)
            self.save_contacts()
            print("Импорт контактов завершен успешно.")
        except (IOError, csv.Error) as e:
            print(f"Ошибка импорта контактов: {e}")

    def export_contacts_csv(self, csv_filepath):
        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'name', 'phone', 'email']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for contact in self.contacts:
                    writer.writerow(contact.to_dict())
            print("Экспорт контактов завершен успешно.")
        except IOError as e:
            print(f"Ошибка экспорта контактов: {e}")


# Модель Финансовой Записи
class FinanceRecord:
    def __init__(self, id, amount, category, date, description):
        self.id = id
        self.amount = amount
        self.category = category
        self.date = date
        self.description = description

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
            "description": self.description
        }

    @staticmethod
    def from_dict(data):
        return FinanceRecord(
            id=data["id"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            description=data["description"]
        )


# Менеджер Финансовых Записей
class FinanceManager:
    def __init__(self, filepath='finance.json'):
        self.filepath = filepath
        self.records = []
        self.load_records()

    def load_records(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    records_data = json.load(f)
                    self.records = [FinanceRecord.from_dict(record) for record in records_data]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки финансовых записей: {e}")
                self.records = []
        else:
            self.records = []

    def save_records(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump([record.to_dict() for record in self.records], f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Ошибка сохранения финансовых записей: {e}")

    def add_record(self, amount, category, date, description):
        try:
            amount = float(amount)
            if amount == 0:
                raise ValueError("Сумма операции не может быть нулевой.")
            if not category.strip():
                raise ValueError("Категория операции не может быть пустой.")
            if not parse_date(date):
                raise ValueError("Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
            new_id = max([record.id for record in self.records], default=0) + 1
            new_record = FinanceRecord(id=new_id, amount=amount, category=category, date=date, description=description)
            self.records.append(new_record)
            self.save_records()
            print("Финансовая запись успешно добавлена.")
        except ValueError as ve:
            print(f"Ошибка: {ve}")

    def list_records(self, filter_by=None):
        filtered_records = self.records
        if filter_by:
            key, value = filter_by
            if key == 'date':
                filtered_records = [record for record in self.records if record.date == value]
            elif key == 'category':
                filtered_records = [record for record in self.records if record.category.lower() == value.lower()]
        if not filtered_records:
            print("Финансовых записей нет.")
            return
        print("\nСписок финансовых записей:")
        for record in filtered_records:
            type_op = "Доход" if record.amount > 0 else "Расход"
            print(
                f"ID: {record.id}, Тип: {type_op}, Сумма: {record.amount}, Категория: {record.category},"
                f" Дата: {record.date}, Описание: {record.description}")

    def generate_report(self, start_date, end_date):
        try:
            start = parse_date(start_date)
            end = parse_date(end_date)
            if not start or not end:
                raise ValueError("Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
            if start > end:
                raise ValueError("Начальная дата не может быть позже конечной.")
            relevant_records = [record for record in self.records if
                                start.strftime("%d-%m-%Y") <= record.date <= end.strftime("%d-%m-%Y")]
            total_income = sum(record.amount for record in relevant_records if record.amount > 0)
            total_expense = sum(record.amount for record in relevant_records if record.amount < 0)
            balance = total_income + total_expense
            print(f"\nОтчёт с {start_date} по {end_date}:")
            print(f"Общий доход: {total_income}")
            print(f"Общий расход: {total_expense}")
            print(f"Баланс: {balance}")

            categories = {}
            for record in relevant_records:
                cat = record.category
                categories[cat] = categories.get(cat, 0) + record.amount
            print("\nГруппировка по категориям:")
            for cat, amt in categories.items():
                type_op = "Доход" if amt > 0 else "Расход"
                print(f"Категория: {cat}, Тип: {type_op}, Сумма: {amt}")
        except ValueError as ve:
            print(f"Ошибка: {ve}")

    def get_balance(self):
        balance = sum(record.amount for record in self.records)
        print(f"\nОбщий баланс: {balance}")

    def import_records_csv(self, csv_filepath):
        try:
            with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    amount = row.get('amount', '').strip()
                    category = row.get('category', '').strip()
                    date = row.get('date', '').strip()
                    description = row.get('description', '').strip()
                    if not amount:
                        print("Пропуск записи без суммы.")
                        continue
                    try:
                        amount = float(amount)
                        if not category:
                            print("Пропуск записи без категории.")
                            continue
                        if not parse_date(date):
                            print(f"Пропуск записи с неверной датой: {date}")
                            continue
                        new_id = max([record.id for record in self.records], default=0) + 1
                        new_record = FinanceRecord(id=new_id, amount=amount, category=category, date=date,
                                                   description=description)
                        self.records.append(new_record)
                    except ValueError:
                        print(f"Пропуск записи с неверной суммой: {amount}")
                        continue
            self.save_records()
            print("Импорт финансовых записей завершен успешно.")
        except (IOError, csv.Error) as e:
            print(f"Ошибка импорта финансовых записей: {e}")

    def export_records_csv(self, csv_filepath):
        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'amount', 'category', 'date', 'description']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for record in self.records:
                    writer.writerow(record.to_dict())
            print("Экспорт финансовых записей завершен успешно.")
        except IOError as e:
            print(f"Ошибка экспорта финансовых записей: {e}")


# Основное Приложение
class PersonalAssistantApp:
    def __init__(self):
        self.note_manager = NoteManager()
        self.task_manager = TaskManager()
        self.contact_manager = ContactManager()
        self.finance_manager = FinanceManager()

    def run(self):
        while True:
            self.show_main_menu()
            choice = input("Введите ваш выбор: ").strip()
            if choice == '1':
                self.manage_notes()
            elif choice == '2':
                self.manage_tasks()
            elif choice == '3':
                self.manage_contacts()
            elif choice == '4':
                self.manage_financial_records()
            elif choice == '5':
                self.run_calculator()
            elif choice == '6':
                print("Выход из приложения. До свидания!")
                break
            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

    def show_main_menu(self):
        print("\nДобро пожаловать в Персональный помощник!")
        print("Выберите действие:")
        print("1. Управление заметками")
        print("2. Управление задачами")
        print("3. Управление контактами")
        print("4. Управление финансовыми записями")
        print("5. Калькулятор")
        print("6. Выход")

    # Управление Заметками
    def manage_notes(self):
        while True:
            print("\nУправление заметками:")
            print("1. Создать новую заметку")
            print("2. Просмотреть список заметок")
            print("3. Просмотреть подробности заметки")
            print("4. Редактировать заметку")
            print("5. Удалить заметку")
            print("6. Импорт заметок из CSV")
            print("7. Экспорт заметок в CSV")
            print("8. Вернуться в главное меню")
            choice = input("Введите ваш выбор: ").strip()
            if choice == '1':
                title = input("Введите заголовок заметки: ")
                content = input("Введите содержимое заметки: ")
                self.note_manager.create_note(title, content)
            elif choice == '2':
                self.note_manager.list_notes()
            elif choice == '3':
                try:
                    note_id = int(input("Введите ID заметки: "))
                    self.note_manager.view_note_details(note_id)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '4':
                try:
                    note_id = int(input("Введите ID заметки для редактирования: "))
                    new_title = input("Введите новый заголовок: ")
                    new_content = input("Введите новое содержимое: ")
                    self.note_manager.edit_note(note_id, new_title, new_content)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '5':
                try:
                    note_id = int(input("Введите ID заметки для удаления: "))
                    self.note_manager.delete_note(note_id)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '6':
                csv_path = input("Введите путь к CSV файлу для импорта: ")
                self.note_manager.import_notes_csv(csv_path)
            elif choice == '7':
                csv_path = input("Введите путь для сохранения CSV файла: ")
                self.note_manager.export_notes_csv(csv_path)
            elif choice == '8':
                break
            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

    # Управление Задачами
    def manage_tasks(self):
        while True:
            print("\nУправление задачами:")
            print("1. Добавить новую задачу")
            print("2. Просмотреть список задач")
            print("3. Отметить задачу как выполненную")
            print("4. Редактировать задачу")
            print("5. Удалить задачу")
            print("6. Импорт задач из CSV")
            print("7. Экспорт задач в CSV")
            print("8. Фильтрация задач")
            print("9. Вернуться в главное меню")
            choice = input("Введите ваш выбор: ").strip()
            if choice == '1':
                title = input("Введите заголовок задачи: ")
                description = input("Введите описание задачи: ")
                print("Выберите приоритет:")
                for idx, pr in enumerate(TaskManager.PRIORITIES, 1):
                    print(f"{idx}. {pr}")
                pr_choice = input("Введите номер приоритета: ").strip()
                try:
                    pr_index = int(pr_choice) - 1
                    if pr_index not in range(len(TaskManager.PRIORITIES)):
                        raise ValueError
                    priority = TaskManager.PRIORITIES[pr_index]
                except ValueError:
                    print("Неверный выбор приоритета. Установлен 'Средний'.")
                    priority = 'Средний'
                due_date = input("Введите срок выполнения (ДД-ММ-ГГГГ): ")
                self.task_manager.add_task(title, description, priority, due_date)
            elif choice == '2':
                self.task_manager.list_tasks()
            elif choice == '3':
                try:
                    task_id = int(input("Введите ID задачи для отметки: "))
                    self.task_manager.mark_task_done(task_id)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '4':
                try:
                    task_id = int(input("Введите ID задачи для редактирования: "))
                    title = input("Введите новый заголовок задачи: ")
                    description = input("Введите новое описание задачи: ")
                    print("Выберите новый приоритет:")
                    for idx, pr in enumerate(TaskManager.PRIORITIES, 1):
                        print(f"{idx}. {pr}")
                    pr_choice = input("Введите номер приоритета: ").strip()
                    try:
                        pr_index = int(pr_choice) - 1
                        if pr_index not in range(len(TaskManager.PRIORITIES)):
                            raise ValueError
                        priority = TaskManager.PRIORITIES[pr_index]
                    except ValueError:
                        print("Неверный выбор приоритета. Установлен 'Средний'.")
                        priority = 'Средний'
                    due_date = input("Введите новый срок выполнения (ДД-ММ-ГГГГ): ")
                    self.task_manager.edit_task(task_id, title, description, priority, due_date)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '5':
                try:
                    task_id = int(input("Введите ID задачи для удаления: "))
                    self.task_manager.delete_task(task_id)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '6':
                csv_path = input("Введите путь к CSV файлу для импорта: ")
                self.task_manager.import_tasks_csv(csv_path)
            elif choice == '7':
                csv_path = input("Введите путь для сохранения CSV файла: ")
                self.task_manager.export_tasks_csv(csv_path)
            elif choice == '8':
                print("\nФильтрация задач по:")
                print("1. Статусу")
                print("2. Приоритету")
                print("3. Сроку выполнения")
                filter_choice = input("Введите ваш выбор: ").strip()
                if filter_choice == '1':
                    status = input("Введите статус (Выполнено/В процессе): ").strip()
                    self.task_manager.filter_tasks('status', status)
                elif filter_choice == '2':
                    priority = input("Введите приоритет (Высокий/Средний/Низкий): ").strip()
                    self.task_manager.filter_tasks('priority', priority)
                elif filter_choice == '3':
                    due_date = input("Введите срок выполнения (ДД-ММ-ГГГГ): ").strip()
                    self.task_manager.filter_tasks('due_date', due_date)
                else:
                    print("Неверный выбор фильтра.")
            elif choice == '9':
                break
            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

    # Управление Контактами
    def manage_contacts(self):
        while True:
            print("\nУправление контактами:")
            print("1. Добавить новый контакт")
            print("2. Поиск контакта")
            print("3. Редактировать контакт")
            print("4. Удалить контакт")
            print("5. Импорт контактов из CSV")
            print("6. Экспорт контактов в CSV")
            print("7. Вернуться в главное меню")
            choice = input("Введите ваш выбор: ").strip()
            if choice == '1':
                name = input("Введите имя контакта: ")
                phone = input("Введите номер телефона: ")
                email = input("Введите email: ")
                self.contact_manager.add_contact(name, phone, email)
            elif choice == '2':
                keyword = input("Введите имя или номер телефона для поиска: ")
                self.contact_manager.search_contacts(keyword)
            elif choice == '3':
                try:
                    contact_id = int(input("Введите ID контакта для редактирования: "))
                    name = input("Введите новое имя контакта: ")
                    phone = input("Введите новый номер телефона: ")
                    email = input("Введите новый email: ")
                    self.contact_manager.edit_contact(contact_id, name, phone, email)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '4':
                try:
                    contact_id = int(input("Введите ID контакта для удаления: "))
                    self.contact_manager.delete_contact(contact_id)
                except ValueError:
                    print("Неверный ID.")
            elif choice == '5':
                csv_path = input("Введите путь к CSV файлу для импорта: ")
                self.contact_manager.import_contacts_csv(csv_path)
            elif choice == '6':
                csv_path = input("Введите путь для сохранения CSV файла: ")
                self.contact_manager.export_contacts_csv(csv_path)
            elif choice == '7':
                break
            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

    # Управление Финансовыми Записями
    def manage_financial_records(self):
        while True:
            print("\nУправление финансовыми записями:")
            print("1. Добавить новую финансовую запись")
            print("2. Просмотреть все записи")
            print("3. Сгенерировать отчёт о финансовой активности")
            print("4. Подсчитать общий баланс")
            print("5. Импорт финансовых записей из CSV")
            print("6. Экспорт финансовых записей в CSV")
            print("7. Вернуться в главное меню")
            choice = input("Введите ваш выбор: ").strip()
            if choice == '1':
                amount = input("Введите сумму операции (положительное для доходов, отрицательное для расходов): ")
                category = input("Введите категорию операции: ")
                date = input("Введите дату операции (ДД-ММ-ГГГГ): ")
                description = input("Введите описание операции: ")
                self.finance_manager.add_record(amount, category, date, description)
            elif choice == '2':
                print("\nФильтрация записей:")
                print("1. Без фильтрации")
                print("2. По дате")
                print("3. По категории")
                filter_choice = input("Введите ваш выбор: ").strip()
                if filter_choice == '1':
                    self.finance_manager.list_records()
                elif filter_choice == '2':
                    date = input("Введите дату для фильтрации (ДД-ММ-ГГГГ): ")
                    self.finance_manager.list_records(filter_by=('date', date))
                elif filter_choice == '3':
                    category = input("Введите категорию для фильтрации: ")
                    self.finance_manager.list_records(filter_by=('category', category))
                else:
                    print("Неверный выбор фильтра.")
            elif choice == '3':
                start_date = input("Введите начальную дату (ДД-ММ-ГГГГ): ")
                end_date = input("Введите конечную дату (ДД-ММ-ГГГГ): ")
                self.finance_manager.generate_report(start_date, end_date)
            elif choice == '4':
                self.finance_manager.get_balance()
            elif choice == '5':
                csv_path = input("Введите путь к CSV файлу для импорта: ")
                self.finance_manager.import_records_csv(csv_path)
            elif choice == '6':
                csv_path = input("Введите путь для сохранения CSV файла: ")
                self.finance_manager.export_records_csv(csv_path)
            elif choice == '7':
                break
            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

    # Калькулятор
    def run_calculator(self):
        print("\nКалькулятор. Выполняет базовые арифметические операции: сложение, вычитание, умножение, деление.")
        print("Введите 'exit' для выхода.")
        while True:
            expr = input("Введите выражение: ").strip()
            if expr.lower() == 'exit':
                break
            try:
                result = self.safe_eval(expr)
                print(f"Результат: {result}")
            except Exception as e:
                print(f"Ошибка вычисления: {e}")

    def safe_eval(self, expr):
        if not re.match(r'^[\d\s\+\-\*\/\(\)]+$', expr):
            raise ValueError("Недопустимые символы в выражении.")

        allowed_operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }

        def parse(tokens):
            def parse_expression(index):
                values = []
                ops = []

                def apply_ops():
                    right = values.pop()
                    left = values.pop()
                    op = ops.pop()
                    values.append(allowed_operators[op](left, right))

                while index < len(tokens):
                    token = tokens[index]
                    if token.isdigit() or ('.' in token and token.replace('.', '', 1).isdigit()):
                        values.append(float(token))
                        index += 1
                    elif token in allowed_operators:
                        while ops and precedence(ops[-1]) >= precedence(token):
                            apply_ops()
                        ops.append(token)
                        index += 1
                    elif token == '(':
                        sub_result, index = parse_expression(index + 1)
                        values.append(sub_result)
                    elif token == ')':
                        break
                    else:
                        raise ValueError(f"Неизвестный токен: {token}")
                while ops:
                    apply_ops()
                return values[0], index + 1

            def precedence(op):
                if op in ('+', '-'):
                    return 1
                elif op in ('*', '/'):
                    return 2
                return 0

            result, _ = parse_expression(0)
            return result

        tokens = re.findall(r'\d+\.\d+|\d+|[+\-*/()]', expr)
        if not tokens:
            raise ValueError("Пустое выражение.")
        return parse(tokens)


if __name__ == "__main__":
    app = PersonalAssistantApp()
    app.run()