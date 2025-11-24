# handlers/registration.py
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from states.user_states import UserRegistration
from database.engine import async_session_maker
from database.models import User

router = Router()

@router.message(UserRegistration.awaiting_display_name)
async def process_display_name(message: types.Message, state: FSMContext):
    display_name = message.text.strip()

    if not display_name or len(display_name) < 2:
        await message.answer("Имя должно быть не короче 2 символов. Попробуй снова:")
        return

    if len(display_name) > 32:
        await message.answer("Имя слишком длинное (макс. 32 символа). Попробуй короче:")
        return

    user = message.from_user

    async with async_session_maker() as session:
        # Создаём или обновляем пользователя
        existing = await session.get(User, user.id)
        if existing:
            existing.display_name = display_name
            existing.username = user.username
            existing.first_name = user.first_name
        else:
            new_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                display_name=display_name
            )
            session.add(new_user)

        await session.commit()

    await message.answer(
        f"Отлично! Теперь все тебя зовут только: <b>{display_name}</b> ✨\n"
        "Ты можешь начать новую игру командой /newgame."
    )
    await state.clear()