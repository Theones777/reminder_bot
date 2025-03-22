import os
from datetime import datetime, date, timedelta

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model
from transliterate import translit

from bot.log import logger
from config import Config


class Users(Model):
    tg_id = fields.IntField(pk=True)
    full_name = fields.CharField(max_length=255)
    tg_user_name = fields.CharField(max_length=255)
    admin = fields.BooleanField(default=False)


class Events(Model):
    id = fields.IntField(pk=True)
    event_name = fields.CharField(max_length=255)
    callback_data = fields.CharField(max_length=255)
    event_date = fields.CharField(max_length=255)
    start_remind_date = fields.CharField(max_length=255)
    term_date = fields.CharField(max_length=255)
    event_info = fields.TextField()


class UserCompletion(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.Users', related_name='completions')
    event = fields.ForeignKeyField('models.Events', related_name='completions', on_delete=fields.CASCADE)
    event_data = fields.TextField()
    create_date = fields.CharField(max_length=255, default=date.today().strftime("%d-%m-%Y"))


class Storage:
    def __init__(self):
        run_async(self.init_db())

    async def init_db(self):
        os.makedirs("data", exist_ok=True)
        await Tortoise.init(db_url=Config.DB_URL, modules={"models": ["bot.clients.storage"]})
        await Tortoise.generate_schemas()
        await Tortoise.get_connection("default").execute_script("PRAGMA journal_mode=WAL;")
        await self.add_column_if_not_exists("Events", "term_date", "VARCHAR(255)")
        logger.info(f"База данных проинициализирована")

    @staticmethod
    async def add_column_if_not_exists(table_name: str, column_name: str, column_type: str):
        connection = Tortoise.get_connection("default")
        info = await connection.execute_query(f"PRAGMA table_info('{table_name}');")
        if column_name not in [row["name"] for row in info[1]]:
            await connection.execute_script(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
            logger.info(f"Новая колонка {column_name} добавлена в {table_name}")

    @staticmethod
    async def _get_callback_data(event_name: str, event_date: str) -> str:
        return translit(event_name + event_date, 'ru', reversed=True).replace(" ", "_")

    @staticmethod
    async def save_new_user(user_id: int, user_full_name: str, tg_user_name: str):
        user, created = await Users.get_or_create(
            tg_id=user_id,
            defaults={"full_name": user_full_name, "tg_user_name": tg_user_name},
        )
        if created:
            logger.info(f"Новый пользователь {user_full_name} добавлен")

    @staticmethod
    async def get_all_users_list() -> list:
        return await Users.all().values_list("tg_id", 'full_name', 'tg_user_name')

    @staticmethod
    async def get_admins_list() -> list:
        return await Users.filter(admin=True).values_list('tg_id', 'full_name', 'tg_user_name')

    @staticmethod
    async def get_admin_ids() -> list:
        return await Users.filter(admin=True).values_list('tg_id', flat=True)

    @staticmethod
    async def add_new_admin(user_id: int):
        user = await Users.filter(tg_id=user_id).first()
        user.admin = True
        await user.save()
        return user.full_name

    @staticmethod
    async def remove_admin(user_id: int):
        admin = await Users.filter(tg_id=user_id).first()
        admin.admin = False
        await admin.save()
        return admin.full_name

    @staticmethod
    async def remove_user(user_id: int):
        user = await Users.filter(tg_id=user_id).first()
        await user.delete()
        return user.full_name

    @staticmethod
    async def get_user_name(user_id: int) -> str:
        user = await Users.filter(tg_id=user_id).first()
        return user.full_name if user.full_name else user.tg_user_name

    @staticmethod
    async def get_events_list() -> str:
        return await Events.all().values_list("id", 'event_name', 'event_date', 'callback_data')

    async def update_events(self, all_events_info: list):
        # update region
        for event_info in all_events_info:
            event_name, event_date, event_data, start_remind_date, term_date = event_info
            callback_data = await self._get_callback_data(event_name, event_date)

            event, created = await Events.get_or_create(
                event_name=event_name,
                callback_data=callback_data,
                event_date=event_date,
                start_remind_date=start_remind_date,
                event_info=event_data,
                term_date=term_date,
                defaults={"event_name": event_name, "event_date": event_date},
            )
            if created:
                logger.info(f"Новое событие {event_name} добавлено")

        # delete region
        for event in await Events.all():
            if datetime.strptime(event.event_date, "%d.%m.%Y") + timedelta(days=Config.EVENT_LIFETIME) < datetime.now():
                logger.info(f"Событие {event.event_name} удалено")
                await event.delete()

    @staticmethod
    async def get_remind_events_info() -> list:
        result = []
        events_info = await Events.all().values_list(
            "event_name",
            "callback_data",
            "event_date",
            "start_remind_date",
            "term_date",
        )
        now = datetime.now()
        for event_info in events_info:
            if datetime.strptime(event_info[-2], "%d.%m.%Y") < now <= datetime.strptime(event_info[-1], "%d.%m.%Y"):
                result.append(event_info[:-2])
        return result

    @staticmethod
    async def get_event_with_callback_data(callback_data: str) -> str:
        event = await Events.filter(callback_data=callback_data).first()
        return event

    @staticmethod
    async def get_filled_events() -> list:
        filled_events = await UserCompletion.all().values_list(
            "user__tg_id",
            "event__event_name",
            "event__event_date",
        )
        return filled_events

    @staticmethod
    async def get_sync_filled_events(event_id: int) -> list:
        event = await Events.filter(id=event_id).first()
        event_data = (event.event_name, event.event_date, event.event_info)

        filled_events_data = await UserCompletion.filter(event__id=event_id).values_list("event_data", flat=True)
        return event_data, filled_events_data

    @staticmethod
    async def remove_event(event_id: int) -> str:
        event = await Events.filter(id=event_id).first()
        await event.delete()
        return event.event_name

    @staticmethod
    async def save_filled_data(user_id: int, user_event_data: str, event_callback_data: str) -> list:
        user_obj = await Users.get(tg_id=user_id)
        event_obj = await Events.get(callback_data=event_callback_data)

        user_event, created = await UserCompletion.get_or_create(
            user=user_obj,
            event=event_obj,
            event_data=user_event_data,
            defaults={"user": user_obj, "event": event_obj, "event_data": user_event_data},
        )
        if created:
            logger.info(f"Событие {event_obj.event_name} заполнено {user_obj.full_name}")
            return True

        return False
