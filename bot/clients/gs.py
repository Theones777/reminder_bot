import asyncio
import gspread
import pandas as pd
from gspread.exceptions import APIError

from bot.log import logger
from config import Config


class EventsClient:
    def __init__(self):
        self.client = gspread.service_account(filename=Config.GS_CONFIG).open(
            Config.GS_SHEET_NAME
        )
    async def _get_events_df(self):
        loop = asyncio.get_running_loop()

        worksheet = await loop.run_in_executor(
            None,
            self.client.worksheet,
            "Список",
        )

        records = await loop.run_in_executor(None, worksheet.get_all_records)
        df = pd.DataFrame(records)
        return df

    async def get_all_events(self):
        df = await self._get_events_df()
        return df.values

    async def insert_sync_df(self, insert_df: pd.DataFrame, page_name: str):
        loop = asyncio.get_running_loop()

        try:
            await loop.run_in_executor(
                None, self.client.add_worksheet, f"{page_name}", 1, 1
            )
            logger.info(f"Создана новая страница {page_name}")
        except APIError:
            pass

        worksheet = await loop.run_in_executor(
            None, self.client.worksheet, f"{page_name}"
        )

        await loop.run_in_executor(
            None,
            worksheet.update,
            [insert_df.columns.values.tolist()] + insert_df.values.tolist(),
        )
