from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states.user_states import UserRegistration
from database.engine import async_session_maker
from database.models import User
from sqlalchemy import select

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext):
    user = message.from_user
    async with async_session_maker() as session:
        # Проверяем, есть ли пользователь в БД
        result = await session.execute(select(User).where(User.id == user.id))
        existing_user = result.scalar_one_or_none()

        if existing_user and existing_user.display_name:
            # Уже зарегистрирован
            await message.answer(
                f"С возвращением, {existing_user.display_name}! 🌟\n"
                "Готов играть? Напиши /newgame, чтобы начать новую игру в рифмы."
            )
            await state.clear()
        else:
            # Нужно зарегистрироваться
            await message.answer(
                "Привет! 👋\n"
                "Пожалуйста, придумай себе творческое имя — оно будет видно другим игрокам.\n"
                "Например: *Рифмач*, *Сонетик*, *Лунный Кот*…\n\n"
                "Напиши своё имя:"
            )
            await state.set_state(UserRegistration.awaiting_display_name)