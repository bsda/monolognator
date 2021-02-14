import imdb
import telegram
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import build_menu

logger = logging.getLogger(__name__)
ia = imdb.IMDb()


def search_movie(movie):
    movies = ia.search_movie(movie)
    return movies


def search_person(person):
    movies = ia.search_person(person)
    return movies


def get_movie(id):
    movie_detail = ia.get_movie(id)
    return movie_detail


def get_person(id):
    person_detail = ia.get_person(id)
    return person_detail


def movie_search_menu(update, context):
    search = update.message.text.split('/movie ')[1]
    movie = search_movie(search)
    buttons = list()
    for m in movie:
        buttons.append(InlineKeyboardButton(f'{m.data.get("title")} - {m.data.get("year")}',
                       callback_data=f'movie,{m.movieID}'))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
    update.message.reply_text('Which one do you mean?', reply_markup=reply_markup)


def person_search_menu(update, context):
    search = update.message.text.split('/person ')[1]
    movie = search_person(search)
    buttons = list()
    for m in movie:
        buttons.append(InlineKeyboardButton(f'{m.data.get("title")} - {m.data.get("year")}',
                       callback_data=f'person,{m.movieID}'))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
    update.message.reply_text('Which one do you mean?', reply_markup=reply_markup)


def movie_info(update, context):
    query = update.callback_query
    mid = query.message.message_id
    cid = query.message.chat_id
    context.bot.delete_message(chat_id=cid, message_id=mid)
    movieid = query.data.split(',')[1]
    try:
        md = get_movie(movieid)
        if md.data.get('directors'):
            directors = [i.data.get('name') for i in md.data.get('directors')]
        else:
            directors = [i.data.get('name') for i in md.data.get('director')]
        cast = [i.data.get('name') for i in md.data.get('cast')[:4]]
        countries = [i for i in md.data.get('countries')]
        air_date = md.data.get('original air date')
        rating = md.data.get('rating')
        votes = md.data.get('votes')
        cover = md.data.get('cover url')
        plot = md.data.get('plot')[0]
        title = md.data.get('title')
        year = md.data.get('year')
        box_office = md.data.get('box office')
        message = f'*{title} - {year} - {", ".join(countries)} *\n'
        message += f'*Rating:* {rating}, *Votes:* {votes}\n'
        message += f"*Directors:* {', '.join(directors)}\n"
        message += f"*Cast:* {', '.join(cast)}\n"
        message += f"*Air Date:* {air_date}\n"
        if box_office:
            budget = box_office.get('Budget')
            gross = box_office.get('Cumulative Worldwide Gross')
            message += f"*Budget:* {budget}\n*Gross:* {gross},\n"
        message += "*Plot:*\n\n"
        message += f"{plot}\n\n"
        message += f'{cover}\n\n'
        logger.info(f'Sending {title}')
    except Exception as e:
        logger.exception(e)
        message = str(e)
    context.bot.send_message(chat_id=cid,
                             text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                             timeout=150)


def person_info(update, context):
    query = update.callback_query
    mid = query.message.message_id
    cid = query.message.chat_id
    context.bot.delete_message(chat_id=cid, message_id=mid)
    person_id = query.data.split(',')[1]
    try:
        pd = get_person(person_id)
        print(pd)
        if pd.data.get('directors'):
            directors = [i.data.get('name') for i in pd.data.get('directors')]
        else:
            directors = [i.data.get('name') for i in pd.data.get('director')]
        cast = [i.data.get('name') for i in pd.data.get('cast')[:4]]
        countries = [i for i in pd.data.get('countries')]
        air_date = pd.data.get('original air date')
        rating = pd.data.get('rating')
        votes = pd.data.get('votes')
        cover = pd.data.get('cover url')
        plot = pd.data.get('plot')[0]
        title = pd.data.get('title')
        year = pd.data.get('year')
        box_office = pd.data.get('box office')
        message = f'*{title} - {year} - {", ".join(countries)} *\n'
        # message += f'*Rating:* {rating}, *Votes:* {votes}\n'
        message += f"*Directors:* {', '.join(directors)}\n"
        message += f"*Cast:* {', '.join(cast)}\n"
        message += f"*Air Date:* {air_date}\n"
        if box_office:
            budget = box_office.get('Budget')
            gross = box_office.get('Cumulative Worldwide Gross')
            message += f"*Budget:* {budget}\n*Gross:* {gross},\n"
        message += "*Plot:*\n\n"
        message += f"{plot}\n\n"
        message += f'{cover}\n\n'
        logger.info(f'Sending {title}')
    except Exception as e:
        logger.exception(e)
        message = str(e)
    context.bot.send_message(chat_id=cid,
                             text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                             timeout=150)