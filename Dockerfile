
FROM python:3
ADD bot.py /
ADD gifs /gifs
RUN pip install pip --upgrade
RUN pip install -r requirements.txt
CMD [ "python3", "./bot.py" ]