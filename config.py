from os import getenv

from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = getenv("BOT_TOKEN")
    GS_CONFIG = getenv("GS_CONFIG")
    GS_SHEET_NAME = getenv("GS_SHEET_NAME")
    ADMIN_PHRASE = getenv("ADMIN_PHRASE")

    DB_URL = getenv("DB_URL", "sqlite://data/database.db")
    EVENT_TEMPLATE_WORKSHEET_PREFIX = getenv("EVENT_TEMPLATE_WORKSHEET_PREFIX", "Шаблон")
    REMIND_TIME = int(getenv("REMIND_TIME", 11))
    DATA_ADMIN = getenv("DATA_ADMIN", "@test")
    SEPARATOR = ";;"
    EVENT_LIFETIME = 60