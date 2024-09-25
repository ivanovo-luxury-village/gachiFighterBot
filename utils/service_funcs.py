import asyncio

class SafeDict(dict):
    def __missing__(self, key):
        '''функция для безопасного форматирования '''
        return (
            f"{{{key}}}"  # если плейсхолдер отсутствует, возвращаем его в исходном виде
        )
    

async def send_messages_with_delay(chat_id: int, messages: list, delay: float):
    '''функция для отправки сообщений с задержкой'''
    for message in messages:
        await bot.send_message(chat_id, message)
        await asyncio.sleep(delay)