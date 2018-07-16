
FROM python:3
ADD bot.py /
ADD gifs /gifs
ENV telegram_token 558631863:AAHCJ_jE6J9ix20Munn6p0AmpfJCQYML7RA
RUN pip install python-telegram-bot
CMD [ "python3", "./bot.py" ]