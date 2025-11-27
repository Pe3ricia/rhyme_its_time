from aiogram import Router, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete
from database.engine import async_session_maker
from database.models import User, GameSession, Player
import re
import secrets
import string

def generate_game_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


router = Router()

class JoinGameStates(StatesGroup):
    waiting_for_game_id = State()

@router.message(Command("newgame"))
async def cmd_newgame(message: types.Message, bot: Bot):
    user = message.from_user

    async with async_session_maker() as session:
        # Находим текущую активную сессию пользователя
        result = await session.execute(
            select(Player)
            .join(GameSession, Player.game_id == GameSession.id)
            .where(Player.user_id == user.id, GameSession.status == "waiting")
        )
        current_player = result.scalar_one_or_none()

        if current_player:
            # Выйти из текущей сессии с оповещениями
            await _leave_session(session, bot, user.id, current_player.game_id)
            await session.commit()  # Сохранить выход перед созданием новой

        # Создаём новую игру
        new_game = GameSession(status="waiting", code=generate_game_code())
        session.add(new_game)
        await session.flush()

        player = Player(user_id=user.id, game_id=new_game.id, order_index=0)
        session.add(player)
        await session.commit()

        await message.answer(
            f"🎭 Игра <b>#{new_game.code}</b> создана!\n\n"
            f"Пришли этот код друзьям:\n"
            f"<code>/join {new_game.code}</code>"
        )


@router.message(Command("join"))
async def cmd_join(message: types.Message, command: Command, state: FSMContext, bot: Bot):
    # Пытаемся получить ID из аргумента
    if command.args:
        match = re.match(r"^([A-Z0-9]{6})$", message.text.strip())
        if match:
            game_code = match.group(1)
            await _process_join(message, bot, game_code, state)
            return

    # Если ID нет — просим прислать его отдельно
    await message.answer(
        "Хорошо! Теперь пришли ID игры.\n"
    )
    await state.set_state(JoinGameStates.waiting_for_game_id)


@router.message(JoinGameStates.waiting_for_game_id)
async def join_game_by_id_message(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text.strip()

    match = re.match(r"^([A-Z0-9]{6})$", text)
    if not match:
        await message.answer(
            "❌ Это не похоже на ID игры.\n"
            "Поробоуй ещё раз"
        )
        return

    game_code = match.group(1)
    await _process_join(message, bot, game_code, state)
    # Состояние автоматически сбросится в _process_join

async def _leave_session(session, bot, user_id: int, game_id: int):
    # Получаем данные для уведомлений
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    name = user.display_name if user else "Игрок"

    # Удаляем игрока
    await session.execute(
        delete(Player).where(Player.user_id == user_id, Player.game_id == game_id)
    )

    # Получаем оставшихся игроков
    remaining = (await session.execute(
        select(Player.user_id).where(Player.game_id == game_id)
    )).scalars().all()

    if not remaining:
        # Удаляем сессию, если игроков нет
        await session.execute(delete(GameSession).where(GameSession.id == game_id))
    else:
        # Уведомляем оставшихся
        for uid in remaining:
            try:
                await bot.send_message(uid, f"👤 Игрок <b>{name}</b> покинул игру.")
            except:
                pass

async def _process_join(message: types.Message, bot, game_code: str, state: FSMContext):
    user = message.from_user

    async with async_session_maker() as session:
        # --- Выход из текущей сессии (если есть) ---
        current_game = (await session.execute(
            select(GameSession)
            .join(Player, Player.game_id == GameSession.id)
            .where(Player.user_id == user.id)
        )).scalar_one_or_none()

        if current_game:
            await _leave_session(session, bot, user.id, current_game.id)
            await session.commit()  # фиксируем выход

        # --- Присоединение к новой ---
        game = (await session.execute(
            select(GameSession).where(GameSession.code == game_code)
        )).scalar_one_or_none()

        if not game or game.status != "waiting":
            await message.answer("❌ Игра не найдена или уже началась.")
            await state.clear()
            return

        # Проверка на дубль (маловероятно, но...)
        existing = (await session.execute(
            select(Player).where(Player.game_id == game.id, Player.user_id == user.id)
        )).scalar_one_or_none()
        if existing:
            await message.answer("Ты уже в этой игре!")
            await state.clear()
            return

        # Добавляем игрока
        player_count = (await session.execute(
            select(Player).where(Player.game_id == game.id)
        )).scalars().all()
        order_index = len(player_count)

        new_player = Player(user_id=user.id, game_id=game.id, order_index=order_index)
        session.add(new_player)
        await session.commit()

        # --- Уведомление о входе ---
        db_user = await session.get(User, user.id)
        name = db_user.display_name if db_user else user.full_name
        all_players = [p.user_id for p in player_count]  # включая нового

        for uid in all_players:
            try:
                await bot.send_message(uid, f"👤 Игрок <b>{name}</b> присоединился к игре!")
            except:
                pass

        await message.answer(f"✅ Ты в игре <b>#{game.code}</b>!")
        await state.clear()

@router.message(Command("leave"))
async def cmd_leave(message: types.Message, bot: Bot):
    user = message.from_user

    async with async_session_maker() as session:
        game = (await session.execute(
            select(GameSession)
            .join(Player, Player.game_id == GameSession.id)
            .where(Player.user_id == user.id)
        )).scalar_one_or_none()

        if not game:
            await message.answer("Ты не участвуешь ни в одной игре.")
            return

        await _leave_session(session, bot, user.id, game.id)
        await session.commit()
        await message.answer("Ты вышел из игры.")