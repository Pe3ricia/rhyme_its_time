from aiogram.fsm.state import State, StatesGroup

class UserRegistration(StatesGroup):
    awaiting_display_name = State()