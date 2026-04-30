import asyncio
import logging
import random
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import load_config
from keyboards.inline_keyboards import (
    after_feedback_keyboard,
    main_menu_keyboard,
    question_keyboard,
    result_keyboard,
)
from services.data_loader import load_animals, load_questions
from services.quiz_service import apply_scores, create_empty_scores, get_result_animal_id
from services.storage import init_db, save_feedback, save_quiz_result, get_last_feedback


BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "images" / "logo.jpeg"

router = Router()

config = load_config()
animals = load_animals()
questions = load_questions()

user_sessions: dict[int, dict] = {}


WELCOME_TEXT = """
Привет! Это викторина «Тотемное животное Московского зоопарка».

Ответьте на несколько вопросов, а я подберу животное, которое больше всего похоже на ваш характер.

В конце вы получите результат, картинку животного и ссылку на программу опеки «Клуб друзей зоопарка».
""".strip()


HELP_TEXT = """
Как пользоваться ботом:

1. Нажмите «Начать викторину».
2. Выбирайте варианты ответов.
3. В конце бот покажет ваше тотемное животное.
4. После результата можно узнать об опеке, поделиться викториной, оставить отзыв или пройти ее заново.

Дополнительные команды:
/animal_fact – случайный факт о животном
/feedbacks – последние отзывы, доступно только администратору

Если что-то пошло не так, отправьте команду /start.
""".strip()


GUARDIANSHIP_TEXT = """
В Московском зоопарке действует программа «Клуб друзей зоопарка».

С ее помощью можно взять животное под опеку и помочь зоопарку заботиться о его обитателях. Опека – это вклад в содержание животных и сохранение биоразнообразия.

Подробнее:
https://moscowzoo.ru/about/guardianship
""".strip()


CONTACTS_TEXT = """
Контакты Московского зоопарка:

Клуб друзей зоопарка:
zoofriends@moscowzoo.ru
+7 (962) 971-38-75

Общие вопросы посетителей:
+7 (495) 775-33-70

Сайт:
https://moscowzoo.ru/contacts
""".strip()


ANIMAL_FACTS = [
    "🐾 Манул выглядит сурово, но именно за этот невозмутимый вид его так любят.",
    "👥 Сурикаты живут группами, поэтому отлично подходят для образа командного игрока.",
    "🦝 Енот-полоскун – символ любопытства: если что-то можно изучить, он обязательно попробует.",
    "🦩 Фламинго напоминает, что выделяться – это не всегда специально, иногда это просто стиль жизни.",
    "🐘 Слон – образ спокойной силы, памяти и надежности.",
    "🦙 Альпака – почти официальный символ уюта, мягкости и мирного настроения.",
    "🌊 Сивуч умеет отдыхать с размахом и заявлять о себе громко.",
    "🌿 Ленивец не спешит – он просто мастерски экономит энергию.",
    "🦧 Орангутан – образ наблюдательности, ума и спокойного анализа.",
]


START_PHRASES = [
    "Готовы узнать, кто вы сегодня: невозмутимый манул, энергичный сурикат или философский орангутан?",
    "Сейчас проверим, какое животное Московского зоопарка ближе всего к вашему характеру.",
    "Внутри каждого из нас есть немного манула, суриката или ленивца. Посмотрим, кто победит сегодня.",
    "Ответьте на несколько вопросов – и узнаете свое тотемное животное.",
    "Добро пожаловать в звериную викторину характера!",
]


def get_user_full_name(message_or_callback) -> str:
    user = message_or_callback.from_user
    parts = [user.first_name, user.last_name]
    return " ".join(part for part in parts if part)


def reset_session(user_id: int) -> None:
    user_sessions[user_id] = {
        "current_question": 0,
        "scores": create_empty_scores(animals),
        "last_result": None,
        "awaiting_feedback": False,
    }


async def send_question(message: Message, user_id: int) -> None:
    session = user_sessions[user_id]
    question_index = session["current_question"]

    if question_index >= len(questions):
        await send_result(message, user_id)
        return

    question = questions[question_index]

    question_icons = ["🌿", "👥", "🧩", "💬", "⭐", "🗨", "🍽", "🏡", "✨"]
    icon = question_icons[question_index] if question_index < len(question_icons) else "❓"

    text = (
        f"🐾 Вопрос {question_index + 1} из {len(questions)}\n\n"
        f"{icon} {question['text']}"
    )

    await message.answer(
        text,
        reply_markup=question_keyboard(question_index, question["answers"]),
    )


async def send_result(message: Message, user_id: int) -> None:
    session = user_sessions[user_id]
    result_animal_id = get_result_animal_id(session["scores"])
    animal = animals[result_animal_id]

    session["last_result"] = result_animal_id

    user = message.chat
    save_quiz_result(
        user_id=user_id,
        username=getattr(user, "username", None),
        full_name=getattr(user, "full_name", str(user_id)),
        animal_id=result_animal_id,
        animal_name=animal["name"],
    )

    image_path = BASE_DIR / animal["image"]

    # Защита на случай, если в animals.json случайно остались символы "\\n"
    result_text = animal["result_text"].replace("\\n", "\n")

    caption = (
        f"{result_text}\n\n"
        f"{GUARDIANSHIP_TEXT}\n\n"
        "Ссылки на животное:\n"
        + "\n".join(animal["links"])
    )

    if image_path.exists():
        await message.answer_animation(
            animation=FSInputFile(image_path),
            caption=caption,
            reply_markup=result_keyboard(config.bot_username),
        )
    else:
        await message.answer(
            caption
            + "\n\n"
            + f"Изображение не найдено: {animal['image']}\n"
            + "Добавьте файл с таким именем в папку images.",
            reply_markup=result_keyboard(config.bot_username),
        )


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    start_text = f"{random.choice(START_PHRASES)}\n\n{WELCOME_TEXT}"

    if LOGO_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(LOGO_PATH),
            caption=start_text,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(
            start_text,
            reply_markup=main_menu_keyboard(),
        )

@router.callback_query(F.data == "animal_fact")
async def callback_animal_fact(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(random.choice(ANIMAL_FACTS))


@router.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("animal_fact"))
async def command_animal_fact(message: Message) -> None:
    await message.answer(random.choice(ANIMAL_FACTS))


@router.message(Command("feedbacks"))
async def command_feedbacks(message: Message) -> None:
    if config.admin_id is None or message.from_user.id != config.admin_id:
        await message.answer("Эта команда доступна только администратору.")
        return

    feedbacks = get_last_feedback(limit=10)

    if not feedbacks:
        await message.answer("Отзывов пока нет.")
        return

    lines = ["Последние отзывы:\n"]

    for index, feedback in enumerate(feedbacks, start=1):
        full_name, username, feedback_text, created_at = feedback
        username_text = f"@{username}" if username else "username не указан"

        lines.append(
            f"{index}. {full_name} ({username_text})\n"
            f"Дата: {created_at}\n"
            f"Отзыв: {feedback_text}\n"
        )

    await message.answer("\n".join(lines))


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "start_quiz")
async def callback_start_quiz(callback: CallbackQuery) -> None:
    await callback.answer()

    user_id = callback.from_user.id
    reset_session(user_id)

    await callback.message.answer("🐾 Начинаем викторину!")
    await send_question(callback.message, user_id)


@router.callback_query(F.data == "restart_quiz")
async def callback_restart_quiz(callback: CallbackQuery) -> None:
    await callback.answer()

    user_id = callback.from_user.id
    reset_session(user_id)

    await callback.message.answer("🔄 Хорошо, попробуем еще раз.")
    await send_question(callback.message, user_id)


@router.callback_query(F.data.startswith("answer:"))
async def callback_answer(callback: CallbackQuery) -> None:
    await callback.answer()

    user_id = callback.from_user.id

    if user_id not in user_sessions:
        reset_session(user_id)

    session = user_sessions[user_id]

    try:
        _, question_index_raw, answer_index_raw = callback.data.split(":")
        question_index = int(question_index_raw)
        answer_index = int(answer_index_raw)
    except (ValueError, AttributeError):
        await callback.message.answer("Не удалось обработать ответ. Попробуйте начать заново: /start")
        return

    if question_index != session["current_question"]:
        await callback.message.answer(
            "Похоже, это ответ на старый вопрос. Продолжим с актуального места."
        )
        await send_question(callback.message, user_id)
        return

    question = questions[question_index]

    if answer_index < 0 or answer_index >= len(question["answers"]):
        await callback.message.answer("Такого варианта ответа нет. Попробуйте начать заново: /start")
        return

    answer = question["answers"][answer_index]

    session["scores"] = apply_scores(session["scores"], answer["scores"])
    session["current_question"] += 1

    if session["current_question"] >= len(questions):
        await send_result(callback.message, user_id)
    else:
        await send_question(callback.message, user_id)


@router.callback_query(F.data == "contact_staff")
async def callback_contact_staff(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()

    user_id = callback.from_user.id
    session = user_sessions.get(user_id, {})
    result_animal_id = session.get("last_result")

    result_text = "Результат викторины пока не определен"
    if result_animal_id and result_animal_id in animals:
        result_text = animals[result_animal_id]["name"]

    username = callback.from_user.username
    full_name = get_user_full_name(callback)

    user_message = (
        "📩 Спасибо! Ниже контакты для связи с Московским зоопарком.\n\n"
        f"Ваш результат: {result_text}\n\n"
        f"{CONTACTS_TEXT}"
    )

    await callback.message.answer(user_message)

    if config.admin_id:
        admin_message = (
            "Пользователь хочет связаться с сотрудником по программе опеки.\n\n"
            f"Имя: {full_name}\n"
            f"Username: @{username if username else 'не указан'}\n"
            f"Telegram ID: {user_id}\n"
            f"Результат викторины: {result_text}"
        )
        await bot.send_message(config.admin_id, admin_message)


@router.callback_query(F.data == "leave_feedback")
async def callback_leave_feedback(callback: CallbackQuery) -> None:
    await callback.answer()

    user_id = callback.from_user.id

    if user_id not in user_sessions:
        reset_session(user_id)

    user_sessions[user_id]["awaiting_feedback"] = True

    await callback.message.answer(
        "✍️ Напишите одним сообщением, что вам понравилось или что можно улучшить."
    )


@router.message(F.text)
async def handle_text_message(message: Message) -> None:
    user_id = message.from_user.id

    if user_id in user_sessions and user_sessions[user_id].get("awaiting_feedback"):
        feedback_text = message.text.strip()

        if len(feedback_text) < 3:
            await message.answer("Отзыв слишком короткий. Напишите чуть подробнее.")
            return

        save_feedback(
            user_id=user_id,
            username=message.from_user.username,
            full_name=get_user_full_name(message),
            feedback_text=feedback_text,
        )

        user_sessions[user_id]["awaiting_feedback"] = False

        await message.answer(
            "Спасибо! Отзыв сохранен.",
            reply_markup=after_feedback_keyboard(),
        )
        return

    await message.answer(
        "Я понимаю команды и кнопки. Чтобы начать, нажмите /start.",
        reply_markup=main_menu_keyboard(),
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())