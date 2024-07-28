from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.googleapi_utils import spreadsheet_id, service
from main import mybot
import datetime as dt

router_servicemen = Router()


class CommandsServCallback(CallbackData, prefix='commands'):
    foo: str


builder_commands_servicemen = InlineKeyboardBuilder()
main_servicemen_button1 = builder_commands_servicemen.button(
    text="Вывести горящие задачи",
    callback_data=CommandsServCallback(foo="/hottasks")
)
main_servicemen_button2 = builder_commands_servicemen.button(
    text="Вывести все актуальные задания",
    callback_data=CommandsServCallback(foo="/alltasks")
)
builder_commands_servicemen.adjust(1)


@router_servicemen.callback_query(
    CommandsServCallback.filter(F.foo == "/alltasks"))
async def callback_actual(query: CallbackQuery):
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    servicemen = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Сервисмены!A:F',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    await query.message.answer("Актуальные заявки:")
    SERV_ID = None
    USER_ID = int(query.from_user.id)
    for submit in output_submit_values:
        surname_serv = str(submit[-2])
        for serv in servicemen:
            if str(serv[1]) == surname_serv:
                SERV_ID = int(serv[0])
                if (SERV_ID == USER_ID) and (submit[5] == "не обработано"):
                    photo_id = str(submit[9]).strip()
                    text = f"Кабинет №{submit[1]}. Заявка №{submit[0]}\n" \
                           f"{submit[2]} – {submit[5]}"
                    if photo_id == 'нет':
                        await query.message.answer(text)
                    elif photo_id != 'нет':
                        await mybot.send_photo(query.message.chat.id, photo=photo_id, caption=text)


@router_servicemen.callback_query(
    CommandsServCallback.filter(F.foo == "/hottasks"))
async def callback_hottasks(query: CallbackQuery):
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    servicemen = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Сервисмены!A:F',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    await query.message.answer(
        "Горящие заявки (до крайнего срока выполнения остается 3 дня):")
    after_three_days = (dt.date.today() + dt.timedelta(days=3)).strftime(
        "%d.%m.%Y")
    SERV_ID = None
    USER_ID = int(query.from_user.id)
    for submit in output_submit_values:
        surname_serv = str(submit[-2])
        for serv in servicemen:
            if str(serv[1]) == surname_serv:
                SERV_ID = int(serv[0])
                if (SERV_ID == USER_ID) and (after_three_days == submit[-3]):
                    photo_id = str(submit[9]).strip()
                    text = f"Кабинет №{submit[1]}. Заявка №{submit[0]}\n" \
                           f"{submit[2]} – {submit[5]}"
                    if photo_id == 'нет':
                        await query.message.answer(text)
                    elif photo_id != 'нет':
                        await mybot.send_photo(query.message.chat.id,
                                               photo=photo_id, caption=text)
