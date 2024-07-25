from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.googleapi_utils import spreadsheet_id, service
from handlers.mainserv_handler import builder_commands_main_servicemen
from handlers.servicemen_handler import builder_commands_servicemen

router = Router()


class MainCallback(CallbackData, prefix='main'):
    foo: str
    bar: str


class CommandsCallback(CallbackData, prefix='commands'):
    foo: str


builder = InlineKeyboardBuilder()
builder.button(
    text="В главное меню",
    callback_data=MainCallback(foo="demo", bar="smth")
)

builder_commands_arend = InlineKeyboardBuilder()
button1 = builder_commands_arend.button(
    text="Оставить заявку",
    callback_data=CommandsCallback(foo="/submit")
)
button2 = builder_commands_arend.button(
    text="Узнать статус заявки",
    callback_data=CommandsCallback(foo="/status")
)
button3 = builder_commands_arend.button(
    text="Получить контакты",
    callback_data=CommandsCallback(foo="/contacts")
)
button4 = builder_commands_arend.button(
    text="Оставить отзыв",
    callback_data=CommandsCallback(foo="/feedback")
)
builder_commands_arend.adjust(1)


@router.message(CommandStart())
async def cmd_start(msg: types.Message) -> None:
    text = "👋 Привет, я твой универсальный помощник по заполнению заявок " \
           "на выполнение обслуживающих работ.\n\n" \
           "Теперь когда в твоем помещении перегорит" \
           " лампочка или заскрипит дверь, " \
           "смело обращайся ко мне 🚀.\n\n Я сделаю так, " \
           "чтобы твоя заявка:\n" \
           "🔹Сохранилась в моей системе\n" \
           "🔹Правильно обработалась и направилась на специалиста\n" \
           "🔹И выполнилась в рамках требуемого времени\n\n" \
           "Хочешь узнать как это сделать? Нажми на кнопку👇"
    USER_ID = int(msg.from_user.id)
    await msg.answer(text=text, reply_markup=builder.as_markup())

    @router.callback_query(MainCallback.filter(F.foo == "demo"))
    async def my_callback_foo(query: CallbackQuery,
                              callback_data: MainCallback):
        arendators_values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Арендаторы!A:G',
            majorDimension='ROWS'
        ).execute()['values'][2:]
        contact = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Контакты!A2:B2',
            majorDimension='ROWS'
        ).execute()['values']
        main_serviceman = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Главный_Сервисмен!A:F',
            majorDimension='ROWS'
        ).execute()['values'][2:]
        servicemen = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Сервисмены!A:F',
            majorDimension='ROWS'
        ).execute()['values'][2:]
        admin_values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Администратор!A:E',
            majorDimension='ROWS'
        ).execute()['values'][2:]
        print(main_serviceman, admin_values)
        list_of_arend_ids = list()
        list_of_servicemen_ids = list()
        text = "✨ Главное меню\n" \
               "Выбери функцию, которая тебе нужна. Если ты потеряешь " \
               "главное меню, просто введи команду /start"
        admin_text = f"✨ {admin_values[0][2]} {admin_values[0][3]}, здравствуйте!\n" \
               "Введите команду /getinfo, чтобы получить информацию о конкретной заявке. "
        for i in range(len(arendators_values)):
            list_of_arend_ids.append(arendators_values[i][0])
        for i in range(len(servicemen)):
            list_of_servicemen_ids.append(servicemen[i][0])

        main_serviceman_id = main_serviceman[0][0]
        if USER_ID == int(main_serviceman_id):  # айди главного
            await query.message.answer(text=text,
                                       reply_markup=builder_commands_main_servicemen.as_markup())
        elif str(USER_ID) == admin_values[0][0]:
            await query.message.answer(text=admin_text)

        elif (USER_ID != int(main_serviceman_id)) and (str(USER_ID) != admin_values[0][0]):
            for i in range(len(arendators_values)):
                print(arendators_values[i][0], type(USER_ID))
                if USER_ID == int(arendators_values[i][0]):
                    await query.message.answer(text=text,
                                               reply_markup=builder_commands_arend.as_markup())
            for i in range(len(servicemen)):
                print(servicemen[i][0], type(USER_ID))
                if USER_ID == int(servicemen[i][0]):
                    await query.message.answer(text=text,
                                               reply_markup=builder_commands_servicemen.as_markup())
        else:
            await query.message.answer(
                "Извините, но вы не являетесь сотрудником компании.\n"
                "Функционал бота доступен только тем, кто зарегистрирован\n"
                f"администратором. Контактный номер: {contact[0][0]}")


@router.callback_query(CommandsCallback.filter(F.foo == "/status"))
async def callback_status(query: CallbackQuery):
    arendators_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Арендаторы!A:G',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    space_number, count = 0, 0

    for arendator in arendators_values:
        if int(query.from_user.id) == int(arendator[0]):
            space_number = int(arendator[-1])

    for submit in output_submit_values:
        if space_number == int(submit[1]):
            await query.message.answer(f"Статус заявки "
                                       f"№{submit[0]} – {submit[5]}")
        if space_number != int(submit[1]):
            count += 1
        if count == len(output_submit_values):
            await query.message.answer(
                f"Актуальных заявок нет")


@router.callback_query(CommandsCallback.filter(F.foo == "/submit"))
async def callback_submit(query: CallbackQuery):
    text = "Чтобы оставить заявку, введи команду /submit"
    await query.message.answer(text=text)


@router.callback_query(CommandsCallback.filter(F.foo == "/feedback"))
async def callback_submit(query: CallbackQuery):
    text = "Чтобы оставить отзыв, введи команду /feedback"
    await query.message.answer(text=text)


@router.callback_query(CommandsCallback.filter(F.foo == "/contacts"))
async def callback_submit(query: CallbackQuery):
    contact = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Контакты!A2:B2',
        majorDimension='ROWS'
    ).execute()['values']
    await query.message.answer(f"Вы можете связаться с нами "
                               f"по номеру телефона: {contact[0][0]}")


@router.message(F.text == '/status')
async def cmd_status(msg: types.Message):
    arendators_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Арендаторы!A:G',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    output_submit_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:J',
        majorDimension='ROWS'
    ).execute()['values'][2:]
    space_number, count = 0, 0
    for arendator in arendators_values:
        if int(msg.from_user.id) == int(arendator[0]):
            space_number = int(arendator[-1])

    for submit in output_submit_values:
        if space_number == int(submit[1]):
            await msg.answer(f"Статус заявки "
                             f"№{submit[0]} – {submit[5]}")
        if space_number != int(submit[1]):
            count += 1
        if count == len(output_submit_values):
            await msg.answer(
                f"Актуальных заявок нет")


@router.message(F.text == '/contacts')
async def cmd_contacts(msg: types.Message):
    contact = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Контакты!A2:B2',
        majorDimension='ROWS'
    ).execute()['values']
    await msg.answer(f"Вы можете связаться с нами "
                     f"по номеру телефона: {contact[0][0]}")
