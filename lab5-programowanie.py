from sqlalchemy import create_engine, select, insert, delete
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, Session, mapped_column
from datetime import datetime

engine = create_engine("sqlite:///todo.db", echo=True)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    status: Mapped[str] = mapped_column(default='do_zrobienia')
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

Base.metadata.create_all(engine)

while True:
    print('\n=== TO DO LIST ===\n')
    wybor = input('Wybierz opcję:\n\n1. Wyświetl listę zadań\n2. Dodaj nowe zadanie\n3. Zmień status zadania\n4. Usuń zadanie\n5. Wyjdź z programu\n\n Opcja №')

    if wybor == '1':
        with Session(engine) as session:
            zadania = session.execute(select(Task)).all()
            if not zadania:
                print('Baza jest pusta!')
            else:
                print("\n=== TABELA TASKS ===")
                print(f"{'ID':<5} | {'TYTUŁ':<25} | {'STATUS':<15} | {'DATA'}")
                print("-" * 65)
                for row in zadania:
                    task = row[0]
                    date_str = task.created_at.strftime("%Y-%m-%d %H:%M")
                    print(f"{task.id:<5} | {task.title:<25} | {task.status:<15} | {date_str}")
 

    elif wybor == '2':
        tytul = input('Wpisz tytuł zadania: ')
        with Session(engine) as session:
            dodaj = session.execute(insert(Task).values(title=tytul))
            print('== DODAWANIE ==')
            print(f'\nZapis został stworzony!\n')
            session.commit()
    elif wybor == '3':
        try:
            id_edit = input('Wpisz numer ID dla edytowania: ')
            id_num = int(id_edit)
            with Session(engine) as session:
                task = session.get(Task, id_num)
                if task:
                    status_edit = input('1. Do zrobienia\n2. W trakcie\n3. Zrobione\nWpisz numer statusu: ')
                    if status_edit == '1':
                        task.status = 'do_zrobienia'
                    elif status_edit == '2':
                        task.status = 'w_trakcie'
                    elif status_edit == '3':
                        task.status = 'zrobione'
                    else:
                        print('Nieprawidłowy numer statusu!')
                    
                    if status_edit in ['1', '2', '3']:
                        session.commit()
                        print('== EDYTOWANIE ==')
                        print('Zadanie zedytowane!')
                else:
                    print('Nie ma takiego zadania!')
        except ValueError:
            print("Błąd: podaj poprawną liczbę!")
        
    elif wybor == "4":
        try:
            id_delete = input('Wpisz numer ID dla edytowania: ')
            with Session(engine) as session:
                task = session.get(Task, int(id_delete))
                if task: 
                    session.delete(task)
                    print('== USUNIĘCIE ==')
                    print(f'Zadanie №{id_delete} zostało usunięte!')
                    session.commit()
                else:
                    print('Zadanie o podanym ID nie istnieje!')
        except ValueError:
            print("Błąd: podaj poprawną liczbę!")
    elif wybor == '5':
        print('Wszystko zostało zapisane!')
        break
    else:
        print('Nie ma takiego polecenia! Podaj inne!')

            


