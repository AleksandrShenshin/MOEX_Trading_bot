# Бот-помощник торговли на MOEX.
Бот умеет отправлять сигналы при выполнении условий:
- достижение ценой заданного значения
- появление объёма на 1m свече >= заданного значения

## Настройка
> [!TIP]
> Перед запуском бота необходимо в файле **.env** установить следующие параметры:
> - **BOT_TOKEN** = 8298363621:AAGKkemhznX0JmbzrIHnjrtaxjTTbFOYLX0 (указываем токен Telegram bot)
> - **FUTURES_LIST** = si, cr (список поддерживаемых фьючерсов)  
В списке указываются первые две буквы тикера (неизменны при смене контракта) через ',' 
> - **TYPES_SIGNAL** = _{'Price': {'param': '-p'}, 'Volume': {'param': '-v'}}_  
(список поддерживаемых сигналов)  
Формат  
_Price, Volume_ - название которое будет видно в боте  
_param_ - -p - price, -v - volume  

> [!WARNING]
> Для работы необходимо в директорию проекта установить следующие пакеты:  
> `pip install -r requirements.txt`  
> `git clone git@github.com:AleksandrShenshin/iss_moex.git`  

## Примеры команд из строки
>>>>>
/get_list_ticker - поддерживаемые тикеры  
/get_signals - список установленных сигналов  
/del <b>id_signal</b> - удалить сигнал по его ID  
/set <b>TICKER</b> <b>TYPE_SIGNAL</b> <b>VALUE</b>  
<b>TICKER</b>: сокращенный (si, cr), полный (siz5)  
<b>TYPE_SIGNAL</b>: -p - price, -v - volume  
<b>VALUE</b>: значение целое или дробное  
<<<<<
