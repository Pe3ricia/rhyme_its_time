# middlewares/registration.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import select
from database.engine import async_session_maker
from database.models import User
from states.user_states import UserRegistration

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Разрешаем /start всегда
        if event.text and event.text.startswith("/start"):
            return await handler(event, data)

        user = event.from_user

        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.id == user.id))
            db_user = result.scalar_one_or_none()

            if not db_user or not db_user.display_name:
                current_state = data["state"]
                state_str = await current_state.get_state()

                if state_str != UserRegistration.awaiting_display_name.state:
                    await event.answer("Сначала придумай себе имя! Напиши /start.")
                    return

        return await handler(event, data)