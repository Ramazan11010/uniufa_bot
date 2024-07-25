from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.googleapi_utils import spreadsheet_id, service
from main import mybot
import datetime


router_submit = Router()
input_text = None
STROKES = [['Заголовок'], ['Заголовок']]
ANSWERS = []


class SubmitFormStates(StatesGroup):
    QUESTION_1 = State()
    QUESTION_2 = State()
    QUESTION_3 = State()
    QUESTION_4 = State()
    QUESTION_5 = State()


class FeedbackFormStates(StatesGroup):
    QUESTION_1 = State()  #
    QUESTION_2 = State()  # +
    QUESTION_3 = State()  # -


@router_submit.message(F.text == "/feedback")
async def cmd_feedback(msg: types.Message, state: FSMContext):
    output_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Арендаторы!A1:G100',
        majorDimension='COLUMNS'
    ).execute()
    arendators_id = output_values['values'][0][2:]
    if str(msg.from_user.id) in arendators_id:
        text = "Режим ввода отзыва.\n" \
               "Введите обратную связь по выполненной работе. " \
               "Опишите общую информацию в этом сообщении, " \
               "а далее, в следующих сообщениях, кратко вводите основные " \
               "плюсы и минусы, которые вы выявили."
        await msg.answer(text=text)
        await state.set_state(FeedbackFormStates.QUESTION_1)
    else:
        await msg.answer("У вас нет доступа к использованию этой команды.")


@router_submit.message(FeedbackFormStates.QUESTION_1)
async def process_feed_q1(msg: types.Message, state: FSMContext):
    try:
        text = "+) Введите плюсы, все то, что вам " \
               "понравилось от работы с ботом, можете описать " \
               "конкретный пример по опыту использования:"
        msg_text = msg.text
        await state.update_data(QUESTION_1=msg_text)
        await state.set_state(FeedbackFormStates.QUESTION_2)
        await msg.answer(text=text)
    except:
        await state.set_state(FeedbackFormStates.QUESTION_1)
        await msg.answer("Системная ошибка")


@router_submit.message(FeedbackFormStates.QUESTION_2)
async def process_feed_q2(msg: types.Message, state: FSMContext):
    try:
        msg_text = msg.text
        await state.update_data(QUESTION_2=msg_text)
        await state.set_state(FeedbackFormStates.QUESTION_3)
        await msg.answer("-) Введите минусы, все то, что вам не понравилось "
                         "от работы с ботом, можете описать конкретный пример "
                         "по опыту использования:")
    except:
        await state.set_state(FeedbackFormStates.QUESTION_2)
        await msg.answer("Системная ошибка")


@router_submit.message(FeedbackFormStates.QUESTION_3)
async def process_feed_q3(msg: types.Message, state: FSMContext):
    try:
        msg_text = msg.text
        await state.update_data(QUESTION_3=msg_text)
        data = await state.get_data()
        list_of = [str(msg.from_user.id), data['QUESTION_1'],
                   data['QUESTION_2'], data['QUESTION_3']]

        output_values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Отзывы!A:D',
            majorDimension='COLUMNS'
        ).execute()['values'][2:]

        idx = len(output_values)

        data_use = [
            {
                "range": f"Отзывы!A{idx + 1}:D",
                "majorDimension": "ROWS",
                "values": [list_of],
            },
        ]
        input_values = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": data_use,
            }
        ).execute()
        await state.clear()
        await msg.answer("Нам важно знать ваше мнение! Спасибо за Ваш отзыв!")
    except:
        await state.set_state(FeedbackFormStates.QUESTION_2)
        await msg.answer("Системная ошибка")


@router_submit.message(F.text == "/submit")
async def cmd_submit(msg: types.Message, state: FSMContext):
    output_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Арендаторы!A1:G100',
        majorDimension='COLUMNS'
    ).execute()
    arendators_id = output_values['values'][0][2:]
    if str(msg.from_user.id) in arendators_id:
        text = "Последовательно вводите информацию.\n" \
               "1. Введите номер арендуемого помещения (например 5):"
        await msg.answer(text=text)
        await state.set_state(SubmitFormStates.QUESTION_1)
    else:
        await msg.answer("У вас нет доступа к использованию этой команды.")


@router_submit.message(SubmitFormStates.QUESTION_1)
async def process_q1(msg: types.Message, state: FSMContext):
    try:
        msg_text = int(msg.text)
        await state.update_data(QUESTION_1=msg_text)
        await state.set_state(SubmitFormStates.QUESTION_2)
        await msg.answer(
            "2. Введите причину обращения (например перегорела лампочка)"
        )
    except ValueError:
        await msg.answer("Нужно было вводить номер помещения. Введи снова.")
        await state.set_state(SubmitFormStates.QUESTION_1)


@router_submit.message(SubmitFormStates.QUESTION_2)
async def process_q2(msg: types.Message, state: FSMContext):
    try:
        if msg.text.isdigit():
            await msg.answer("Нужно было ввести текст. Введи снова.")
            await state.set_state(SubmitFormStates.QUESTION_2)
        else:
            msg_text = str(msg.text)
            await state.update_data(QUESTION_2=msg_text)
            await state.set_state(SubmitFormStates.QUESTION_3)
            await msg.answer(
                '3. Описание проблемы (кратко опиши ситуацию, '
                'из-за чего она могла возникнуть)'
            )
    except ValueError:
        if not msg.text.isdigit():
            await msg.answer("Нужно было ввести текст. Введи снова.")
            await state.set_state(SubmitFormStates.QUESTION_2)


@router_submit.message(SubmitFormStates.QUESTION_3)
async def process_q3(msg: types.Message, state: FSMContext):
    try:
        if msg.text.isdigit():
            await msg.answer("Нужно было ввести текст. Введи снова.")
            await state.set_state(SubmitFormStates.QUESTION_3)
        else:
            msg_text = str(msg.text)
            await state.update_data(QUESTION_3=msg_text)
            await state.set_state(SubmitFormStates.QUESTION_4)
            await msg.answer(
                '4. Отправь нам фотографию инцидента (необязательно). Если ее '
                'нет, введи слово "нет" (без кавычек)'
            )
    except ValueError:
        await msg.answer("Нужно было ввести текст. Введи снова.")
        await state.set_state(SubmitFormStates.QUESTION_3)


@router_submit.message(SubmitFormStates.QUESTION_4)
async def process_q4(msg: types.Message, state: FSMContext):
    photo_ids = []
    if msg.text == 'нет' or msg.text == 'Нет' or msg.text == 'НЕТ':
        await state.update_data(QUESTION_4=msg.text)
        await state.set_state(SubmitFormStates.QUESTION_5)
        await msg.answer(
            '5. Оставь свой контактный номер телефона (пример 89999999999)'
        )
    elif msg.photo:
        try:
            photo = msg.photo[-1]
            photo_ids.append(photo.file_id)
            await mybot.get_file(photo.file_id)
            await msg.answer('Фото было успешно сохранено!')
            await state.update_data(QUESTION_4=photo.file_id)
            await state.set_state(SubmitFormStates.QUESTION_5)
            await msg.answer(
                '5. Оставь свой контактный номер телефона (пример 89999999999)'
            )
        except Exception as e:
            await msg.answer(f'Ошибка при сохранении фото: {str(e)}')
    else:
        await msg.answer(
            "Простите, я вас не понял, повторите снова отправить "
            "фото или введите слово 'нет'(без кавычек)")
        await state.set_state(SubmitFormStates.QUESTION_4)


@router_submit.message(SubmitFormStates.QUESTION_5)
async def process_q5(msg: types.Message, state: FSMContext):
    output_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Заявки!A:A',
        majorDimension='COLUMNS'
    ).execute()
    count = len(output_values['values'][0][2:]) + 2 \
        if len(output_values['values'][0]) != 1 else 2
    IDS = output_values['values'][0] \
        if len(output_values['values'][0]) != 1 else []
    try:
        msg_text = int(msg.text)
        await state.update_data(QUESTION_5=msg_text)
        ANSWERS = await state.get_data()
        await msg.answer("Спасибо, данные записаны, ждите обратного звонка!")
        idi = 0
        if len(IDS) == 0:
            idi = 100000
        elif idi not in IDS:
            idi = int(IDS[-1]) + 1
        IDS.append(idi)

        DICT = {
            'id': idi,
            'q1': ANSWERS['QUESTION_1'],
            'q2': ANSWERS['QUESTION_2'],
            'q3': ANSWERS['QUESTION_3'],
            'q4': ANSWERS['QUESTION_4'],
            'q5': ANSWERS['QUESTION_5'],
            'status': 'не обработано',
            'date': datetime.date.today().strftime("%d.%m.%Y"),
            'deadline': (datetime.date.today() +
                         datetime.timedelta(days=7)).strftime("%d.%m.%Y"),
        }
        list_of = [DICT['id'], DICT['q1'], DICT['q2'], DICT['q3'], DICT['q5'],
                   DICT['status'], DICT['date'], DICT['deadline'], None, DICT['q4']]
        STROKES.append(list_of)
        data = [
            {
                "range": f"A{count + 1}:J{count + 1}",
                "majorDimension": "ROWS",
                "values": [list_of],
            },
        ]
        input_values = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": data,
            }
        ).execute()
        await state.clear()
    except ValueError:
        await msg.answer("Нужно было вводить числовое значение. Введи снова.")
        await state.set_state(SubmitFormStates.QUESTION_4)
