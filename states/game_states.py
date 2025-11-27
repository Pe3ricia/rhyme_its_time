from aiogram.fsm.state import State, StatesGroup

class GameStates(StatesGroup):
    waiting_for_players = State()
    waiting_for_first_line = State()