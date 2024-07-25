from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()
TOKEN = os.getenv('TOKEN')
mybot = Bot(token=TOKEN)


async def main():
    from handlers.initial_handler import router
    from handlers.submit_handler import router_submit
    from handlers.mainserv_handler import mainserv_router
    from handlers.servicemen_handler import router_servicemen
    from handlers.admin_handler import router_admin
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(router_submit)
    dp.include_router(mainserv_router)
    dp.include_router(router_servicemen)
    dp.include_router(router_admin)
    await dp.start_polling(mybot)


if __name__ == '__main__':
    asyncio.run(main())
