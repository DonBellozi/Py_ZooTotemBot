from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐾 Начать викторину", callback_data="start_quiz")],
            [InlineKeyboardButton(text="🆘 Помощь", callback_data="help")],
        ]
    )


def question_keyboard(question_index: int, answers: list[dict]) -> InlineKeyboardMarkup:
    buttons = []

    for answer_index, answer in enumerate(answers):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=answer["text"],
                    callback_data=f"answer:{question_index}:{answer_index}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def result_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    share_text = (
        "🐾 Я прошел викторину Московского зоопарка и узнал свое тотемное животное! "
        f"Попробуй и ты: https://t.me/{bot_username}"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="ℹ️ Узнать об опеке",
                    url="https://moscowzoo.ru/about/guardianship",
                )
            ],
            [InlineKeyboardButton(text="📩 Связаться с сотрудником", callback_data="contact_staff")],
            [
                InlineKeyboardButton(
                    text="📢 Поделиться результатом",
                    url=f"https://t.me/share/url?url=https://t.me/{bot_username}&text={share_text}",
                )
            ],
            [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="leave_feedback")],
            [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data="restart_quiz")],
        ]
    )


def after_feedback_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data="restart_quiz")],
            [InlineKeyboardButton(text="ℹ️ Узнать об опеке", url="https://moscowzoo.ru/about/guardianship")],
        ]
    )
