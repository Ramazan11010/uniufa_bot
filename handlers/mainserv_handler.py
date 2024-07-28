from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.googleapi_utils import spreadsheet_id, service
from main import mybot

mainserv_router = Router()


class ChangeFormStates(StatesGroup):
    QUESTION_1 = State()
    QUESTION_2 = State()


class RedirectFormStates(StatesGroup):
    QUESTION_1 = State()
    QUESTION_2 = State()


ANSWERS_CHANGE = []
ANSWERS_REDIRECT = []
EMPLOYEE = ''


class CommandsCallback(CallbackData, prefix='commands'):
    foo: str


class ServicemenCallback(CallbackData, prefix='commands'):
    foo: str


builder_commands_main_servicemen = InlineKeyboardBuilder()
main_servicemen_button1 = builder_commands_main_servicemen.button(
    text="Вывести актуальные заявки",
    callback_data=CommandsCallback(foo="/actual")
)
main_servicemen_button2 = builder_commands_main_servicemen.button(
    text="Изменить статус заявки",
    callback_data=CommandsCallback(foo="/change")
)
main_servicemen_button3 = builder_commands_main_servicemen.button(
    text="Перенаправить заявку",
    callback_data=CommandsCallback(foo="/redirect")
)
builder_commands_main_servicemen.adjust(1)


@mainserv_router.callback_query(CommandsCallback.filter(F.foo == "/actual"))
async def callback_actual(query: CallbackQuery):
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    await query.message.answer("Актуальные заявки:")

    for submit in output_submit_values:
        if submit[5] == "не обработано":
            photo_id = str(submit[9]).strip()
            text = f"Заявка №{submit[0]}\n" \
                   f"{submit[2]} – {submit[5]}"
            if photo_id == 'нет':
                await query.message.answer(text)
            elif photo_id != 'нет':
                await mybot.send_photo(query.message.chat.id, photo=photo_id,
                                       caption=text)


@mainserv_router.callback_query(CommandsCallback.filter(F.foo == "/change"))
async def callback_change(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Изменение статуса заявки")
    text = "Введите номер заявки, статус которой нужно изменить:"
    await query.message.answer(text=text)
    await state.set_state(ChangeFormStates.QUESTION_1)


@mainserv_router.message(ChangeFormStates.QUESTION_1)
async def process_q1(msg: types.Message, state: FSMContext):
    try:
        msg_text = int(msg.text)
        await state.update_data(QUESTION_1=msg_text)
        await msg.answer("Введите в текстовое поле ввода новый "
                         "статус из списка, соблюдая правила орфографии, "
                         "без лишних символов, без кавычек:\n"
                         "'не обработано'\n"
                         "'в процессе'\n"
                         "'выполнено'\n"
                         "'просрочено'")
        await state.set_state(ChangeFormStates.QUESTION_2)
    except ValueError:
        await msg.answer("Нужно было вводить номер заявки. Введи снова.")
        await state.set_state(ChangeFormStates.QUESTION_1)


@mainserv_router.message(ChangeFormStates.QUESTION_2)
async def process_q2(msg: types.Message, state: FSMContext):
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    try:
        msg_text = str(msg.text)
        await state.update_data(QUESTION_2=msg_text)
        ANSWERS_CHANGE = await state.get_data()
        answer_1 = ANSWERS_CHANGE['QUESTION_1']
        answer_2 = ANSWERS_CHANGE['QUESTION_2']
        for i in range(len(output_submit_values)):
            if int(answer_1) == int(output_submit_values[i][0]):
                data = [
                    {
                        "range": f"F{i + 3}:G{i + 3}",
                        "majorDimension": "ROWS",
                        "values": [[answer_2]],
                    },
                ]
                input_values = service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        "valueInputOption": "USER_ENTERED",
                        "data": data,
                    }
                ).execute()
                await msg.answer("Статус успешно изменен")
        await state.clear()
    except ValueError:
        await msg.answer("Ошибка ввода")
        await state.set_state(ChangeFormStates.QUESTION_2)


@mainserv_router.callback_query(CommandsCallback.filter(F.foo == "/redirect"))
async def callback_redirect(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Перенаправление заявки:")
    text = "Введите номер заявки, которую нужно перенаправить исполнителю:"
    await query.message.answer(text=text)
    await state.set_state(RedirectFormStates.QUESTION_1)


@mainserv_router.message(RedirectFormStates.QUESTION_1)
async def process_red_q1(msg: types.Message, state: FSMContext):
    try:
        msg_text = int(msg.text)
        await state.update_data(QUESTION_1=msg_text)
        await state.set_state(RedirectFormStates.QUESTION_2)
        await msg.answer("Введите фамилию сервисмена.")
    except ValueError as e:
        await msg.answer(
            "Нужно было вводить номер заявки. Введите снова.")
        await state.set_state(RedirectFormStates.QUESTION_1)
        print(f"Error occured: {e}")


@mainserv_router.message(RedirectFormStates.QUESTION_2)
async def process_red_q2(msg: types.Message, state: FSMContext):
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    servicemen_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Сервисмены!A:F',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    try:
        msg_text = str(msg.text)
        await state.update_data(QUESTION_2=msg_text)
        data = await state.get_data()
        for submit in output_submit_values:
            idi = int(submit[0])
            if int(data["QUESTION_1"]) == idi:
                for employee in servicemen_values:
                    if str(data["QUESTION_2"]) == employee[1]:
                        user_id = employee[0]
                        text = f"{employee[2]} {employee[3]}, вам " \
                               f"направлена заявка " \
                               f"№{submit[0]} – {submit[3]} "
                        await mybot.send_message(chat_id=user_id, text=text)
        for submit in output_submit_values:
            idi_sub = int(submit[0])
            index = output_submit_values.index(submit)
            if int(data["QUESTION_1"]) == idi_sub:
                data_input = [
                    {
                        "range": f"I{index + 3}:I{index + 3}",
                        "majorDimension": "ROWS",
                        "values": [[str(data["QUESTION_2"])]],
                    },
                ]
                input_values = service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        "valueInputOption": "USER_ENTERED",
                        "data": data_input,
                    }
                ).execute()
                await msg.answer("Заявка успешно перенаправлена!")
                await state.clear()
    except ValueError as e:
        await msg.answer(
            "Нужно было вводить фамилию сервисмена с заглавной буквы. "
            "Попробуйте ввести ее снова.")
        await state.set_state(RedirectFormStates.QUESTION_2)
        print(f"Error occured: {e}")
