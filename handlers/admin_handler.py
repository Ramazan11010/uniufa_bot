from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData
from utils.googleapi_utils import spreadsheet_id, service
from main import mybot


router_admin = Router()


class DetailFormStates(StatesGroup):
    QUESTION_1 = State()


class CommandsAdminCallback(CallbackData, prefix='commands'):
    foo: str


@router_admin.message(F.text == "/getinfo")
async def callback_getinfo(msg: types.Message, state: FSMContext):
    await msg.answer("Режим вывода детальной информации")
    text = "Введите номер заявки, детальную информацию которой нужно вывести:"
    await msg.answer(text=text)
    await state.set_state(DetailFormStates.QUESTION_1)


@router_admin.message(DetailFormStates.QUESTION_1)
async def process_getinfo_q1(msg: types.Message, state: FSMContext):
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    try:
        msg_text = int(msg.text)
        await state.update_data(QUESTION_1=msg_text)
        for i in range(len(output_submit_values)):
            submit = output_submit_values[i]
            submit_id = int(output_submit_values[i][0])
            if submit_id == msg_text:
                photo_id = str(submit[9]).strip()
                text = f"Заявка №{submit[0]}\n" \
                       f"{submit[2]} – {submit[5]}"
                if photo_id == 'нет':
                    await msg.answer(text)
                elif photo_id != 'нет':
                    await mybot.send_photo(msg.chat.id,
                                           photo=photo_id, caption=text)
        await state.clear()
    except ValueError:
        await msg.answer("Нужно было вводить номер заявки. Введите снова.")
        await state.set_state(DetailFormStates.QUESTION_1)
