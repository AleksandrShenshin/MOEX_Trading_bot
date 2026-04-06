# Бот-помощник торговли на MOEX.
Бот умеет отправлять сигналы при выполнении условий:
- достижение ценой заданного значения
- появление объёма на 1m свече >= заданного значения
- поиск инструмента с 5м свечой значительно превышающей по размеру предыдущие
- поиск пробросов

## Настройка
> [!TIP]
> Перед запуском бота необходимо в файле **.env** установить следующие параметры:
> - **MAX_BOT_TOKEN** = 8298363621:AAGKkemhznX0JmbzrIHnjrtaxjTTbFOYLX0 (указываем токен MAX bot)  
> - **MAX_USER_ID** = 198198198  
> - **T_TOKEN** = 8298363621:AAGKkemhznX0JmbzrIHnjrtaxjTTbFOYLX0 (указываем токен T invest)  
> - **FUTURES_LIST** = si, cr (список поддерживаемых фьючерсов)  
В списке указываются первые две буквы тикера (неизменны при смене контракта) через ',' 
> - **TYPES_SIGNAL** = _{'Price': {'param': '-p'}, 'Volume': {'param': '-v'}, 'Long5': {'param': '-c'}}_  
(список поддерживаемых сигналов)  
Формат  
_Price, Volume, Long5_ - название которое будет видно в боте  
_param_ - -p - price, -v - volume, -c - long5  
> - **CANDLE_FORTS** = BR, GD, SV, NG, MX, Si, BM, CR, RI, FF, SF, MM 	
> - **CANDLE_MOEX** = SBER, VTBR, GAZP, GMKN, OZON, SMLT, YDEX, LKOH  

> [!WARNING]
> Для работы необходимо в директорию проекта установить следующие пакеты:  
> `pip install -r requirements.txt`  

## Примеры команд из строки
>>>>>
/start - запуск Бота  
/stop - остановка Бота  
/menu - главное меню с кнопками  
/help - показать список комманд  
/get_signals - список установленных сигналов  
/del id_signal - удалить сигнал по его ID  
/set TICKER TYPE_SIGNAL VALUE  
        TICKER: сокращенный (si, cr), полный (siz5)  
        TYPE_SIGNAL: -p - price, -v - volume  
        VALUE: значение целое или дробное  
/long5 forts/moex  
/get_list_ticker - поддерживаемые тикеры  
/debug PARAM  
PARAM может принимать следующие значения:  
        get_tasks - получить id опрашиваемых сигналов  
<<<<<
