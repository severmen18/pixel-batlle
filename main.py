import json
from fastapi import FastAPI, Request, WebSocket
from fastapi.templating import Jinja2Templates
from sqlalchemy import cast, extract, func, select, update, delete, exists, or_, not_, and_, Integer, func
from sqlalchemy.exc import NoResultFound
from starlette.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from models.models import Matrix, User, MyConsts
from typing import List
from datetime import timedelta, datetime
from models.base import SessionLocal

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
db = SessionLocal()

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}



@app.get("/matrix")
async def get_matrix():
    # matrix = db.scalars(select(Matrix).order_by(Matrix.id))

    query = db.query(Matrix.y_position,Matrix.x_position, Matrix.color, User.name).join(User, User.id == Matrix.user_point, isouter=True).order_by(Matrix.id)
    return query.all()

@app.get('/faculty-statistics')
async def faculty_statistics():
    """
        Получение статистики по факультетам
        0 Энерго
        1 Фист
        2 Эконом
        3 Ртф
        4 Стройфак 
        5 Гум
        6 Машфак
        7 ИФМИ
        8 ИАТУ
    """
    result = []
    query = db.query(User.faculty, func.count(Matrix.id)).join(Matrix, Matrix.user_point == User.id).group_by(User.faculty)
    for one_faculty in query.all():
        result.append({
            "faculty": one_faculty[0],
            "count": one_faculty[1]
        })
    return result


class ConnectionManager:

    def get_active_users(self) -> list:
        return list(self.active_connections.values())
    def __init__(self):
        self.active_connections: dict[WebSocket] = {}

    async def connect(self, websocket: WebSocket, base_user_info: dict):
        await websocket.accept()
        self.active_connections[websocket] = base_user_info

    def disconnect(self, websocket: WebSocket):
        del self.active_connections[websocket]

    async def send_personal_json(self, json, websocket: WebSocket):
        await websocket.send_json(json)

    async def broadcast(self, message):
        for connection in self.active_connections.keys():
            try:
                await connection.send_json(message)
            except Exception as ex:
                print(f"Ошибка неизвестного характера{ex}")

manager = ConnectionManager()


async def check_charges_count(consts:list, user: User) -> User:
    shot_count = db.query(MyConsts).where(MyConsts.name == "shot_count").one()
    recharge_time = db.query(MyConsts).where(MyConsts.name == "recharge_time").one()
    user_last_shot = user.last_shot

    if user.charges_count == 0:
        if user_last_shot + timedelta(seconds=recharge_time) < datetime.now():
            #обновляем выстрелы
            db.execute(update(User).values(User.charges_count == shot_count)
                       .where(User.id == user.id))
            db.commit()
            user.charges_count = shot_count
    return user

async def get_base_user_info(user: User) -> dict:
    last_user_point = await get_user_last_point(user)
    base_user_info = {}
    if last_user_point is not None:
        base_user_info['last_user_point_x'] = last_user_point.x_position
        base_user_info['last_user_point_y'] = last_user_point.y_position
    base_user_info['name'] = user.name
    base_user_info['id'] = user.id
    base_user_info['skin'] = user.skin
    return base_user_info

async def get_user_last_point(user: User) -> Matrix:
    '''
        Получение x, y элемента матрицы на которую он поставил точку
    '''
    query = db.query(Matrix).join(User, User.id == Matrix.user_point).where(User.id == user.id).order_by(Matrix.update_datetime).limit(1)
    return query.one_or_none()

@app.websocket("/ws")
async def websocket_endpoint( vk_id: str, name:str, faculty: str | None,  websocket: WebSocket):
    user = list(db.scalars(select(User).where(User.vk_id == vk_id)))
    consts: list = [{const.name: const.value} for const in await get_all_consts()]
    if len(user) == 0:
        user = User(name=name, vk_id=vk_id, faculty=faculty, point_count=0)
        db.add(user)
        db.commit()
    else:
        user = user[0]

    base_user_info = await get_base_user_info(user)
    await manager.connect(websocket, base_user_info)
    #всем сооющение что появилься новый пользователь
    await manager.broadcast({
        "type": 'new_user',
        "user": await get_base_user_info(user)
    })
    try:
        active_users = manager.get_active_users()
        await manager.send_personal_json({"const" : consts, "skin": user.skin,
                                          "charges_count": user.charges_count,
                                          'active_users': active_users,
                                          'id': base_user_info['id']}, websocket=websocket)
        while True:
            data = await websocket.receive_json()
            consts: list = [{const.name: const.value} for const in await get_all_consts()]
            user = await check_charges_count(consts, user)
            if user.charges_count != 0:
                await new_point(data, user)
                await manager.broadcast({**data, "id": base_user_info['id'] } )
            else:
                await manager.send_personal_json({'error': 'У вас нету выстрелов'}, websocket=websocket)
            # await manager.send_personal_message(f"You wrote: {data}", websocket)


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # await manager.broadcast(f"Client #{client_id} left the chat")

async def get_all_consts() -> list:
    return list(db.scalars(select(MyConsts)))


async def new_point(data, user):
    db.execute(update(Matrix).values(color=data['color'], user_point=user.id)
               .where(and_(Matrix.y_position == data['y_position'], Matrix.x_position == data['x_position'])))
    db.execute(update(User).values(point_count=User.point_count + 1, charges_count = User.charges_count - 1).where(User.id == user.id))
    db.commit()
