
FROM python:3
ADD bot.py /
ADD gifs /gifs
RUN pip install python-telegram-bot
CMD [ "python3", "./bot.py" ]