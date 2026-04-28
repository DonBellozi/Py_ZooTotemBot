from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    admin_id: int | None
    bot_username: str


def load_config() -> Config:
    """
    Загружает настройки из .env.

    BOT_TOKEN обязателен.
    ADMIN_ID можно не указывать, тогда заявка на связь просто покажет контакты зоопарка.
    BOT_USERNAME нужен для текста "поделиться".
    """
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Не указан BOT_TOKEN. Создайте .env на основе .env.example")

    admin_id_raw = os.getenv("ADMIN_ID", "").strip()
    admin_id = int(admin_id_raw) if admin_id_raw.isdigit() else None

    bot_username = os.getenv("BOT_USERNAME", "your_bot_username").strip().lstrip("@")

    return Config(
        bot_token=bot_token,
        admin_id=admin_id,
        bot_username=bot_username,
    )
