from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, Session
from sqlalchemy.orm import mapped_column
from sqlalchemy import insert, func, ForeignKey, select, bindparam, cast, String
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
scalar_subq = (select(Client.name)
               .where(Client.channel_type == bindparam('type'))
               .scalar_subquery())
stmt = select(scalar_subq)
with Session(engine) as session:
    res = session.execute(stmt, {'type': 'Reels'}).scalar()
    print(f'Client: {res}')

stmt2 = select(Order.title, Order.price).where(Order.price > bindparam('price'))

with Session(engine) as session:
    res = session.execute(stmt2, {'price': 100})
    for title, price in res:
        print(f'Project: {title} | Price: ${price}')

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

