from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, Session
from sqlalchemy.orm import mapped_column, aliased
from sqlalchemy import insert, func, ForeignKey, select, bindparam, cast, String, desc
from typing import List
from sqlalchemy.orm import relationship


engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

#Creating
class Base(DeclarativeBase):
    pass

class Client(Base):
    __tablename__ = 'clients'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    channel_type: Mapped[str]
    orders: Mapped[List[Order]] = relationship(back_populates='client')

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    price: Mapped[int]
    status: Mapped[str]
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'))
    client: Mapped[Client] = relationship(back_populates='orders')

Base.metadata.create_all(engine)

#Inserting
with Session(engine) as session:
    session.execute(insert(Client), [
        {'name': 'Vlad', 'channel_type': 'Reels'},
        {'name': 'Sasha', 'channel_type': 'YouTube'},
        {'name': 'Proshine', 'channel_type': 'TikTok'}
    ])
    session.commit()

with Session(engine) as session:
    session.execute(insert(Order), [
        {'title': 'Reel', 'price': 150, 'status': 'completed', 'client_id': 1},
        {'title': 'YouTube Long', 'price': 500, 'status': 'in_progress', 'client_id': 2},
        {'title': 'TikTok Intro', 'price': 80, 'status': 'completed', 'client_id': 3},
        {'title': 'Reel Motion VFX', 'price': 200, 'status':'pending', 'client_id': 4}
    ])
    session.commit()

#Selecting

#task1
scalar_subq = (select(Client.name)
               .where(Client.channel_type == bindparam('type'))
               .scalar_subquery())
stmt = select(scalar_subq)
with Session(engine) as session:
    res = session.execute(stmt, {'type': 'Reels'}).scalar()
    print(f'Client: {res}')

#task2
stmt2 = select(Order.title, Order.price).where(Order.price > bindparam('price'))

with Session(engine) as session:
    res = session.execute(stmt2, {'price': 100})
    for title, price in res:
        print(f'Project: {title} | Price: ${price}')

#task3
res = ('Order: ' + Order.title + " ($" + cast(Order.price, String) + ")").label('order_info')
stmt3 = select(res).order_by(Order.title)
with Session(engine) as session:
    for row in session.execute(stmt3):
        print(f'{row.order_info}')

#Joins/Agg
with Session(engine) as session:
    q1 = select(Order.title, Client.name).join(Client).where(Order.status == 'completed')
    for title, name in session.execute(q1):
        print(f'Project: {title} | Client: {name}')
    q2 = select(Order.title, Order.price).select_from(Client).join(Order, Client.id == Order.client_id)
    for title, price in session.execute(q2):
        print(f'Project: {title} | Price: {price}')
    q3 = select(Client.name, Order.title).select_from(Client).join(Order, Client.id == Order.client_id, isouter=True)
    for name, title in session.execute(q3):
        print(f'Client: {name} | Project: {title}')
    q4 = select(func.count('*')).select_from(Order)
    total = session.execute(q4).scalar()
    print(f'Total count: {total}')

#Group By/Having/Subquery/CTEs

#task1
task1 = (select(Client.name, func.sum(Order.price).label('total_spent'))
         .join(Order)
         .group_by(Client.name)
         .having(func.sum(Order.price) > 100)
         .order_by(desc('total_spent')))
with Session(engine) as session:
    for name, total in session.execute(task1):
        print(f'Client Name: {name} | Total earned: {total}')

#task2
o1 = aliased(Order)
o2 = aliased(Order)
task2 = (select(o1.title, o1.price, o2.title, o2.price)
         .join_from(o1, o2, o1.price > o2.price)
         )
with Session(engine) as session:
    for t1, p1, t2, p2 in session.execute(task2):
        print(f'"{t1}" (${p1}) more expensive than "{t2}" (${p2})')

#task3
subq = select(func.avg(Order.price)).scalar_subquery()

with Session(engine) as session:
    task3 = select(Order.title, Order.price).where(Order.price > subq)
    for title, price in session.execute(task3):
        print(f'Order: {title} | Price: ${price}')

#task4
subq = (
    select(Client.id, Client.name, func.count(Order.id).label('count'))
    .join(Order, Client.id == Order.client_id)
    .group_by(Client.id, Client.name)
    .cte()
)

with Session(engine) as session:
    task4 = (select(Client.name, subq.c.count)
             .join_from(Client, subq, Client.id == subq.c.id))
    for name, count in session.execute(task4):
        print(f'Name: {name} | Total orders: {count}')

#task5
subq = select(func.max(Order.price).label('max_price')).scalar_subquery()
with Session(engine) as session:
    task5 = select(Order.title, Client.name, Order.price).join(Client).where(Order.price == subq)
    for title, name, price in session.execute(task5):
        print(f'Order: {title} | Client name: {name} | Price: {price}')


#task6
subq = (
    select(Client.id, Client.name, func.sum(Order.price).label('total_spent'))
    .join(Order, Client.id == Order.client_id)
    .group_by(Client.id, Client.name)
    .cte()
)
avg_price_subq = select(func.avg(Order.price)).scalar_subquery()

with Session(engine) as session:
    task6 = select(Client.name, subq.c.total_spent).join_from(Client, subq, Client.id == subq.c.id).where(subq.c.total_spent > avg_price_subq)
    for name, spent in session.execute(task6):
        print(f'Client: {name} | Total spent: {spent}')

#task7
count_subq = (
    select(Client.id, Client.name, func.count(Order.status).label('count'))
    .join(Order)
    .where(Order.status == 'completed')
    .group_by(Client.id, Client.name)
    .cte()

    )
with Session(engine) as session:
    task7 = (
        select(Client.name, count_subq.c.count)
        .join_from(Client, count_subq, Client.id == count_subq.c.id)
        )
    for name, count in session.execute(task7):
        print(f'Client: {name} | Completed orders: {count}')