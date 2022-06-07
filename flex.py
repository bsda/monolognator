# -*- coding: utf-8 -*-

import logging
import pymysql
import config
import sys
import telegram
import plotly.express as px
import pandas as pd
import json
from math import ceil, floor
from operator import itemgetter
import datetime
from pymysql.cursors import DictCursor
import plotly.graph_objects as go
from pymysql.constants import CLIENT
import random
import colorsys



cfg = config.cfg()

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def all_dates():
    start_date = datetime.date(2022, 1, 1)
    end_date = datetime.date.today()  # perhaps date.now()

    delta = end_date - start_date  # returns timedelta

    all = [str(start_date + datetime.timedelta(days=i)) for i in range(delta.days + 1)]
    return all


def progression(modality):
#     1+roundup((hoje-1jan22)*.5)
    today = datetime.date.today()
    day = int(today.strftime('%j'))
    days = range(1, day)
    dates = all_dates()
    inc = 0
    flex = 1
    prog = list()
    for i in dates:
        date = datetime.datetime.strptime(i, '%Y-%m-%d')
        day = int(date.strftime('%j'))
        if modality == 'prata':
            inc += 0.5
            # if inc == 1:
            #     flex += 1
            #     inc = 0
            flex = floor(day * 0.5)
            # print(f'{i}: {flex}')
        elif modality == 'nanica':
            inc += 1
            if inc == 7:
                flex += 2
                inc = 0
            # flex = floor(day * 0.5)
            # print(f'{i}: {flex}')

        prog.append({'username': 'progression', 'flex': flex, 'date': i})
    return prog


def prog_sum():
    prog = progression()




def db_connect():
    conv = pymysql.converters.conversions.copy()
    conv[246] = float  # convert decimals to floats
    conv[10] = str
    try:
        conn = pymysql.connect(
            host=cfg.get('flex_db_host'),
            user=cfg.get('flex_db_user'),
            passwd=cfg.get('flex_db_password'),
            db=cfg.get('flex_db'),
            connect_timeout=5,
            conv=conv,
            client_flag=CLIENT.MULTI_STATEMENTS
        )

        return conn
    except Exception as e:
        logger.error(f'Could not connect to MySQL instance: {e}')
        sys.exit()


def get_percent_all():
    conn = db_connect()
    query = '''
    select u.username,  CAST(round((count(distinct(c.date)) / datediff(date(now()), '2021-12-31' ) * 100)) AS SIGNED) pct from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    group by u.username
    order by pct desc
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_flex_day(user):
    conn = db_connect()
    query = '''
    select u.username, CAST(sum(flex_done) AS SIGNED) flex, date from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    where lower(u.username)=lower(%s)
    group by username, date
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query, user)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_period_flex(period):
    conn = db_connect()
    if period in ['day', 'today', 'hoje']:
        where = 'date = curdate()'
    elif period in ['yesterday', 'ontem']:
        where = 'date = curdate()-1'
    elif period in ['daybeforeyesterday', 'thedaybeforeyesterday', 'anteontem']:
        where = 'date = curdate()-2'
    elif period in ['daybeforedaybeforeyesterday', 'thedaybeforethedaybeforeyesterday', 'anteanteontem']:
        where = 'date = curdate()-3'
    elif period in ['week', 'semana']:
        where = 'YEARWEEK(date, 1) = YEARWEEK(CURDATE(), 1)'
    elif period in ['month', 'mes']:
        where = 'MONTH(date) = MONTH(CURDATE())'
    query = f'''
    select u.username, CAST(sum(flex_done) AS SIGNED) flex from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    where {where}
    group by username
    order by flex asc
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_flex_day_split(user):
    conn = db_connect()
    query = '''
    select u.username, flex_done AS flex, date
    from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    where lower(u.username)=lower(%s)
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query, user)

            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_flex_day_all():
    conn = db_connect()
    query = '''
    select u.username, CAST(sum(flex_done) AS SIGNED) flex, date from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    group by username, date
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_flex_sum(modality):
    conn = db_connect()
    query = '''
    select u.username, CAST(sum(flex_done) AS SIGNED) flex from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    join CHPX_modalities m on u.ID_modality = m.ID_modality 
    where m.modality = %s
    group by username
    order by flex
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query, modality)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_users():
    conn = db_connect()
    query = '''
    select u.username from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    group by username
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_modality(user):
    conn = db_connect()
    query = '''
    select m.modality from CHPX_modalities m
    join CHPX_users u on u.ID_modality = m.ID_modality 
    where lower(u.username) = lower(%s)
    '''
    try:
        with conn.cursor() as cursor:
            rows = cursor.execute(query, user)
            if rows:
                result = cursor.fetchone()[0]
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_flex_hours_all():
    conn = db_connect()
    query = '''
    select u.username, CAST(sum(flex_done) AS SIGNED) flex, date, hour(datetime) AS hour from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    group by hour, username, date
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def get_flex_datetime_all():
    conn = db_connect()
    query = '''
    select u.username, CAST(sum(flex_done) AS SIGNED) flex, date, datetime from CHPX_contributions c
    join CHPX_users u on c.ID_user = u.ID_user
    group by username, datetime
    '''
    try:
        with conn.cursor(cursor=DictCursor) as cursor:
            rows = cursor.execute(query)
            if rows:
                result = cursor.fetchall()
            else:
                return {}
    except Exception as e:
        logger.error(f'Request does not exist: {e}')
        pass
    else:
        return result


def add_empty_dates(derp):
    derp = derp
    dates = all_dates()
    user = derp[0]['username']
    for d in dates:
      if not any(f['date'] == d for f in derp):
          derp.append({'username': user, 'flex': 0, 'date': d, })
    derp = sorted(derp, key=itemgetter('date'))
    return derp


def generate_flex_graph(user):
    modality = get_modality(user)
    prog = progression(modality)
    flex = get_flex_day(user)
    # flex.extend(prog)
    prog_df = pd.read_json(json.dumps(prog))
    new_flex = add_empty_dates(flex)
    df = pd.read_json(json.dumps(new_flex))
    total = df['flex'].sum()
    fig = px.bar(
        df,
        x='date',
        y='flex',
        color='username',
        title=f'{total} flex',
        text='flex'
    )
    fig.add_trace(
        go.Scatter(
        x=prog_df['date'],
        y=prog_df['flex'],
        name='daily expected'
    ))
    # fig.show()
    fig.write_image(f'{user}.png', width=1200, height=675)


def generate_flex_graphs(user_list):
    modality_list = list()
    new_flex = list()
    for user in user_list:
        modality_list.append(get_modality(user))
        flex = get_flex_day(user)
        new_flex += add_empty_dates(flex)
        # print(new_flex)
        # print(pd.read_json(json.dumps(new_flex)))
    df = pd.read_json(json.dumps(new_flex))
    total = df['flex'].sum()
    fig = px.bar(
        df,
        x='date',
        y='flex',
        color='username',
        title=f'{total} flex',
        barmode='group',
        text='flex'
    )
    for modality in list(set(modality_list)):
        prog = progression(modality)
        prog_df = pd.read_json(json.dumps(prog))
        fig.add_trace(
            go.Scatter(
            x=prog_df['date'],
            y=prog_df['flex'],
            name=f'daily expected ({modality})'
        ))
    # fig.show()
    image_name = f'{"_".join(user_list)}.png'
    fig.write_image(image_name, width=1200, height=675)
    return image_name


def generate_flex_graph_split(user):

    modality = get_modality(user)
    prog = progression(modality)
    flex = get_flex_day_split(user)
    flex = increase_sentada(flex)
    # flex.extend(prog)
    prog_df = pd.read_json(json.dumps(prog))
    new_flex = add_empty_dates(flex)
    df = pd.read_json(json.dumps(new_flex))
    total = df['flex'].sum()
    df['set'] = df['set'].astype('Int64').astype('str')
    fig = px.bar(
        df,
        x='date',
        y='flex',
        color='set',
        title=f'{user}: {total} flex',
        text='flex',
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.add_trace(
        go.Scatter(
        x=prog_df['date'],
        y=prog_df['flex'],
        name='daily expected'
    ))
    # fig.show()
    fig.write_image(f'{user}.png', width=1200, height=675)


def generate_flex_graph_all():
    flex = get_flex_day_all()
    new_flex = add_empty_dates(flex)
    df = pd.read_json(json.dumps(new_flex))
    total = df['flex'].sum()
    fig = px.bar(
        df,
        x='date',
        y='flex',
        color='username',
        title=f'{total} flex',
    )
    # fig.show()
    fig.write_image('all.png', width=1200, height=675)


def add_sum_line(fig, sum_, flex):
    fig.add_shape(type='line',
                  x0=-1,
                  y0=sum_,
                  x1=len(flex),
                  y1=sum_,
                  line=dict(color='Red', dash='dot', width=2),
                  xref='x',
                  yref='y',
                  name='expected')


def generate_combined_standings(modality):
    sum_list = [sum([i['flex'] for i in progression(banana)]) for banana in ['nanica', 'prata']]
    flex = sorted(get_flex_sum('nanica')+get_flex_sum('prata'), key=lambda x: x['flex'])
    df = pd.read_json(json.dumps(flex))
    total = df['flex'].sum()
    fig = px.bar(
        df,
        x='username',
        y='flex',
        color='username',
        title=f'{modality} Standings',
        text='flex',
        color_discrete_sequence=px.colors.qualitative.Alphabet
    )
    for sum_ in sum_list:
        add_sum_line(fig, sum_, flex)
    # fig.show()
    fig.write_image(f'{modality}.png', width=1200, height=675)


def generate_standings(modality):
    if modality in ['nanicaprata', 'pratananica']:
        generate_combined_standings(modality)
        return
    else:
        dates = progression(modality)
    sum_ = 0
    for i in dates:
        sum_ += i['flex']
    flex = get_flex_sum(modality)
    df = pd.read_json(json.dumps(flex))
    total = df['flex'].sum()
    fig = px.bar(
        df,
        x='username',
        y='flex',
        color='username',
        title=f'{modality} Standings',
        text_auto=True


    )
    fig.update_layout(legend={'traceorder': 'reversed'})
    add_sum_line(fig, sum_, flex)
    fig.show()
    fig.write_image(f'{modality}.png', width=1200, height=675)


def hsv_to_hex(h, s, v):
    return '#%02x%02x%02x'%tuple([int(i*255) for i in colorsys.hsv_to_rgb(h, s, v)])


def get_accum_flex(include_zero=True):
    flex = get_flex_day_all()
    user_list = list({item['username'] for item in flex}) # get_users()
    date_list = sorted({item['date'] for item in flex}) # all_dates()
    
    half_user_len = int(1+len(user_list)/2)
    user_color_table = [hsv_to_hex(float(i)/half_user_len, 1.0, 1.0) for i in range(half_user_len)]
    user_color_table += [hsv_to_hex(float(i+0.5)/half_user_len, 0.5, 1.0) for i in range(half_user_len)]
    random.seed(1234)
    random.shuffle(user_color_table)

    flex_dict = dict()
    for user in user_list:
        flex_dict[user] = dict([(item['date'], item['flex']) for item in get_flex_day(user)])
        for date in date_list:
            if not date in flex_dict[user]:
                flex_dict[user][date] = 0

    user_dict = dict()
    date_to_user_dict = dict()
    for user_id, user in enumerate(user_list):
        user_dict[user] = dict()
        user_dict[user]['color'] = user_color_table[user_id%len(user_color_table)]
        user_dict[user]['date_list'] = date_list
        user_dict[user]['accum'] = []
        user_dict[user]['x'] = []
        user_dict[user]['y'] = []
        for date_id, date in enumerate(date_list):
            last_flex = user_dict[user]['accum'][-1] if len(user_dict[user]['accum']) > 0 else 0
            accum = last_flex+flex_dict[user][date]
            if accum > 0:
                if last_flex == 0 and date_id > 0 and include_zero:
                    user_dict[user]['x'].append(date_list[date_id-1])
                    user_dict[user]['y'].append(0)
                    user_dict[user]['accum'].append(0)
                    if date in date_to_user_dict:
                        date_to_user_dict[date_list[date_id-1]].append(user)
                    else:
                        date_to_user_dict[date_list[date_id-1]] = [user]
                user_dict[user]['x'].append(date)
                user_dict[user]['y'].append(accum)
                user_dict[user]['accum'].append(accum)
                if date in date_to_user_dict:
                    date_to_user_dict[date].append(user)
                else:
                    date_to_user_dict[date] = [user]

    return user_dict, date_to_user_dict


def get_accum_flex2(include_zero=True):
    flex = get_flex_datetime_all()
    user_list = list({item['username'] for item in flex}) # get_users()
    date_list = sorted({item['datetime'] for item in flex}) # all_dates()
    
    half_user_len = int(1+len(user_list)/2)
    user_color_table = [hsv_to_hex(float(i)/half_user_len, 1.0, 1.0) for i in range(half_user_len)]
    user_color_table += [hsv_to_hex(float(i+0.5)/half_user_len, 0.5, 1.0) for i in range(half_user_len)]
    random.seed(1234)
    random.shuffle(user_color_table)

    flex_dict = dict()
    for item in flex:
        if item['username'] not in flex_dict:
            flex_dict[item['username']] = {item['datetime']: item['flex']}
        else:
            flex_dict[item['username']][item['datetime']] = item['flex']

    for user in user_list:
        for date in date_list:
            if not date in flex_dict[user]:
                flex_dict[user][date] = 0

    user_dict = dict()
    date_to_user_dict = dict()
    for user_id, user in enumerate(user_list):
        user_dict[user] = dict()
        user_dict[user]['color'] = user_color_table[user_id%len(user_color_table)]
        user_dict[user]['date_list'] = date_list
        user_dict[user]['x'] = []
        user_dict[user]['y'] = []
        user_dict[user]['accum'] = []
        user_dict[user]['flex'] = []
        for date_id, date in enumerate(date_list):
            last_flex = user_dict[user]['accum'][-1] if len(user_dict[user]['accum']) > 0 else 0
            accum = last_flex+flex_dict[user][date]
            if accum > 0:
                if False: # last_flex == 0 and date_id > 0 and include_zero:
                    user_dict[user]['x'].append(date_list[date_id-1])
                    user_dict[user]['y'].append(0)
                    user_dict[user]['accum'].append(0)
                    user_dict[user]['flex'].append(flex_dict[user][date_list[date_id-1]])
                    if date_list[date_id-1] in date_to_user_dict:
                        date_to_user_dict[date_list[date_id-1]].append(user)
                    else:
                        date_to_user_dict[date_list[date_id-1]] = [user]
                user_dict[user]['x'].append(date)
                user_dict[user]['y'].append(accum)
                user_dict[user]['accum'].append(accum)
                user_dict[user]['flex'].append(flex_dict[user][date])
                if date in date_to_user_dict:
                    date_to_user_dict[date].append(user)
                else:
                    date_to_user_dict[date] = [user]
            elif include_zero:
                user_dict[user]['x'].append(date)
                user_dict[user]['y'].append(accum)
                user_dict[user]['accum'].append(accum)
                user_dict[user]['flex'].append(flex_dict[user][date])
                if date in date_to_user_dict:
                    date_to_user_dict[date].append(user)
                else:
                    date_to_user_dict[date] = [user]

    return user_dict, date_to_user_dict


def generate_top_day_flex(top_count):
    flex = get_flex_day_all()
    user_list = list({item['username'] for item in flex}) # get_users()
    date_list = sorted({item['date'] for item in flex}) # all_dates()

    half_user_len = int(1+len(user_list)/2)
    user_color_table = [hsv_to_hex(float(i)/half_user_len, 1.0, 1.0) for i in range(half_user_len)]
    user_color_table += [hsv_to_hex(float(i+0.5)/half_user_len, 0.5, 1.0) for i in range(half_user_len)]
    random.seed(1234)
    random.shuffle(user_color_table)

    flex_dict = dict()
    for user in user_list:
        user_flex = get_flex_day(user)
        if user_flex is not None:
            flex_dict[user] = dict([(item['date'], item['flex']) for item in user_flex])
            for date in date_list:
                if not date in flex_dict[user]:
                    flex_dict[user][date] = 0
        else:
            flex_dict[user] = dict([(date, 0) for date in date_list])
    
    fig = go.Figure()

    fig_data = []
    for i in range(top_count):
        flex = []
        data = {'date':[], 'flex':[], 'username':[], 'color':[]}
        date_to_flex_user_dict = dict()
        for date_id, date in enumerate(date_list):
            date_to_flex_user_dict[date] = []
            for user_id, user in enumerate(user_list):
                date_to_flex_user_dict[date].append([flex_dict[user][date], user])
            date_to_flex_user_dict[date] = sorted(date_to_flex_user_dict[date])[::-1][i:i+1]
            for item in date_to_flex_user_dict[date]:
                flex.append({'flex': item[0], 'username': item[1], 'date': date})
                data['date'].append(date)
                data['flex'].append(item[0])
                data['username'].append(item[1])
                user_id = user_list.index(item[1])
                data['color'].append(user_color_table[user_id%len(user_color_table)])
        df = pd.read_json(json.dumps(flex))
        fig.add_trace(
            go.Bar(
                name='',
                x=data['date'],
                y=data['flex'],
                marker={'color': data['color']},
                text=data['username'],
                textangle=90,
                offsetgroup=i,
                showlegend=False
            ))
    
    for user_id, user in enumerate(user_list):
        fig.add_trace(go.Bar(name=user, x=[date], y=[0], marker={'color': [user_color_table[user_id%len(user_color_table)]]}))

    fig.update_layout(title=f'Flex - Top {top_count}', bargap=0.40)

    # fig.show()
    fig.write_image('topday.png', width=2400, height=1350) #, width=1200, height=675) #, width=4800, height=2700) #


def lower_list(list_upper):
    if list_upper is None:
        return list_upper
    return [item.lower() for item in list_upper]


def has_user(user, user_filter_list):
    if user_filter_list is None:
        return True
    return user.lower() in user_filter_list


def generate_accum_graph(user_filter_list=None):
    fig = go.Figure()
    user_dict, date_to_user_dict = get_accum_flex()
    for user in sorted(user_dict.keys(), key=lambda x: user_dict[x]['accum'][-1])[::-1]:
        if has_user(user, user_filter_list):
            fig.add_trace(go.Scatter(x=user_dict[user]['x'], y=user_dict[user]['y'],
                mode='lines', name=user, line=dict(color=user_dict[user]['color'])))
    fig.update_layout(title='Flex - Accumulated Graph - '+('All' if user_filter_list is None else ' '.join(user_filter_list)))
    fig.write_image('accum.png', width=2400, height=1350)


def generate_accum2_graph(user_filter_list=None):
    fig = go.Figure()
    user_dict, date_to_user_dict = get_accum_flex2(include_zero=False)
    for user in sorted(user_dict.keys(), key=lambda x: user_dict[x]['accum'][-1])[::-1]:
        if has_user(user, user_filter_list):
            # user_dict[user]['y'] = sorted(set(user_dict[user]['y']))
            fig.add_trace(go.Scatter(x=user_dict[user]['x'], y=user_dict[user]['y'],
                mode='lines', name=user, line=dict(color=user_dict[user]['color'])))
    fig.update_layout(title='Flex - Accumulated Graph - '+('All' if user_filter_list is None else ' '.join(user_filter_list)))
    fig.write_image('accum2.png', width=2400, height=1350)


def get_rank_list(date, date_list, user_list, user_dict, date_to_user_dict):
    rank_list = []
    for user_id, user in enumerate(user_list):
        if user in date_to_user_dict[date]:
            date_id = user_dict[user]['x'].index(date)
            rank_list.append([user_dict[user]['accum'][date_id], user_id, user])
    return rank_list


def generate_accum100_graph(user_filter_list=None):
    fig = go.Figure()
    user_dict, date_to_user_dict = get_accum_flex()
    last_day_rank_list = sorted([[user_dict[user]['accum'][-1], user] for user in user_dict.keys()])
    user_list = [user for accum, user in last_day_rank_list]
    date_list = user_dict[user_list[0]]['date_list']
    for date in date_list:
        rank_list = get_rank_list(date, date_list, user_list, user_dict, date_to_user_dict)
        if len(rank_list) > 0:
            ranked_user_list = [user for accum, user_id, user in rank_list]
            if user_filter_list is None:
                accum_max = max([accum for accum, user_id, user in rank_list])
            else:
                accum_max = max([accum for accum, user_id, user in rank_list if user.lower() in user_filter_list])
            for user in ranked_user_list:
                date_id = user_dict[user]['x'].index(date)
                user_dict[user]['y'][date_id] = float(user_dict[user]['accum'][date_id])/accum_max if accum_max > 0 else 0
    for accum, user in last_day_rank_list[::-1]:
        if has_user(user, user_filter_list):
            fig.add_trace(go.Scatter(x=user_dict[user]['x'], y=user_dict[user]['y'],
                mode='lines', name=user, line=dict(color=user_dict[user]['color'])))
    fig.update_layout(title='Flex - Accumulated Percentage Graph - '+('All' if user_filter_list is None else ' '.join(user_filter_list)))
    fig.write_image('accum100.png', width=1200, height=675)


def generate_f1_graph(user_filter_list=None):
    fig = go.Figure()
    user_dict, date_to_user_dict = get_accum_flex(include_zero=False)
    last_day_rank_list = sorted([[user_dict[user]['accum'][-1], user] for user in user_dict.keys()])
    if user_filter_list is None:
        user_list = [user for accum, user in last_day_rank_list]
    else:
        user_list = [user for accum, user in last_day_rank_list if user.lower() in user_filter_list]
    date_list = user_dict[user_list[0]]['date_list']
    for date in date_list:
        rank_list = get_rank_list(date, date_list, user_list, user_dict, date_to_user_dict)
        if len(rank_list) > 0:
            ranked_user_list = [user for accum, user_id, user in sorted(rank_list) if accum > 0]
            for rank, user in enumerate(ranked_user_list):
                date_id = user_dict[user]['x'].index(date)
                user_dict[user]['y'][date_id] = rank
    for accum, user in last_day_rank_list[::-1]:
        if has_user(user, user_filter_list):
            fig.add_trace(go.Scatter(x=user_dict[user]['x'], y=user_dict[user]['y'],
                mode='lines', name=user, line=dict(color=user_dict[user]['color'])))
    fig.update_layout(title='Flex - Rank Graph - '+('All' if user_filter_list is None else ' '.join(user_filter_list)))
    fig.write_image('f1graph.png', width=1200, height=675)


def generate_f1_graph2(user_filter_list=None):
    fig = go.Figure()
    user_dict, date_to_user_dict = get_accum_flex2(include_zero=False)
    last_day_rank_list = sorted([[user_dict[user]['accum'][-1], user] for user in user_dict.keys()])
    if user_filter_list is None:
        user_list = [user for accum, user in last_day_rank_list]
    else:
        user_list = [user for accum, user in last_day_rank_list if user.lower() in user_filter_list]
    date_list = user_dict[user_list[0]]['date_list']
    for date in date_list:
        rank_list = get_rank_list(date, date_list, user_list, user_dict, date_to_user_dict)
        if len(rank_list) > 0:
            ranked_user_list = [user for accum, user_id, user in sorted(rank_list) if accum > 0]
            for rank, user in enumerate(ranked_user_list):
                date_id = user_dict[user]['x'].index(date)
                user_dict[user]['y'][date_id] = rank
    for accum, user in last_day_rank_list[::-1]:
        if has_user(user, user_filter_list):
            fig.add_trace(go.Scatter(x=user_dict[user]['x'], y=user_dict[user]['y'],
                mode='lines', name=user, line=dict(color=user_dict[user]['color'])))
    fig.update_layout(title='Flex - Rank Graph - '+('All' if user_filter_list is None else ' '.join(user_filter_list)))
    fig.write_image('f1graph2.png', width=1200, height=675)


def generate_hour_graph(user_filter_list=None):
    fig = go.Figure()
    flex = get_flex_hours_all()
    user_list = list({item['username'] for item in flex}) # get_users()
    date_list = sorted({item['date'] for item in flex}) # all_dates()
    hour_list = sorted({item['hour'] for item in flex})
    hour_label_list = ['%02d:00'%hour for hour in hour_list][::-1]
    z_list = [[0 for date in date_list] for hour in hour_list]
    for item in flex:
        if user_filter_list is None or (user_filter_list is not None and item['username'].lower() in user_filter_list):
            date_id = date_list.index(item['date'])
            hour = 23-(item['hour']+5)%24 # Manual offset of reported hours!
            z_list[hour][date_id] += item['flex']
    # z_label_list = [[str(z_list[hour_id][date_id]) for date_id, date in enumerate(date_list)] for hour_id, hour in enumerate(hour_list)]
    fig.add_trace(
        go.Heatmap(
        x=date_list,
        y=hour_label_list,
        z=z_list,
        type='heatmap',
        # text=z_label_list,
        colorscale='Electric'
        # Blackbody,Bluered,Blues,Cividis,Earth,Electric,Greens,Greys,Hot,Jet,Picnic,Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
    ))
    fig.update_layout(title='Flex - Hour Heatmap - '+('All' if user_filter_list is None else ' '.join(user_filter_list)))
    fig.write_image(f'hourgraph.png', width=1200, height=675)


def generate_period(period, user_filter_list=None):
    flex = get_period_flex(period)
    if user_filter_list is not None:
        flex = [item for item in flex if item['username'].lower() in user_filter_list]
    df = pd.read_json(json.dumps(flex))
    if period in ['day', 'today', 'hoje']:
        title = f'Flexes on {datetime.date.today()}'
    elif period in ['yesterday', 'ontem']:
        title = f'Flexes on {datetime.date.today()-datetime.timedelta(days=1)}'
    elif period in ['daybeforeyesterday', 'thedaybeforeyesterday', 'anteontem']:
        title = f'Flexes on {datetime.date.today()-datetime.timedelta(days=2)}'
    elif period in ['daybeforedaybeforeyesterday', 'thedaybeforethedaybeforeyesterday', 'anteanteontem']:
        title = f'Flexes on {datetime.date.today()-datetime.timedelta(days=3)}'
    elif period in ['week', 'semana']:
        title = 'Flexes na semana'
    elif period in ['month', 'mes']:
        title = 'Flexes no mes'
    fig = px.bar(
        df,
        x='username',
        y='flex',
        color='username',
        text='flex',
        title=title,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        legend={'traceorder': 'reversed'},
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="Black"))

    # fig.show()
    fig.write_image('period.png', width=1200, height=675)


def send_percent_all(update, context):
    results =  get_percent_all()

    text = f'*% dias meta cumprida*\n\n'
    for i in results:
        text += f'{i["username"]}: {i["pct"]}%\n'
    context.bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def generate_help_message():
    text = '/flex - gráfico de barras coloridinhas de todos\n'
    text += '/flex user1 [[user2] [user3] ..] - gráfico de barras individual(is)\n'
    text += '/flex [nanica|prata|nanicaprata|pratananica] - acumulado total de índios em bananas\n'
    text += '/flex accum [[user1] [user2] ..] - curva acumulada, geral ou individual(is), por dia\n'
    text += '/flex accum2 [[user1] [user2] ..] - curva acumulada, geral ou individual(is), por entradas\n'
    text += '/flex accum100 [[user1] [user2] ..] - curva acumulada, percentual do máximo diário, geral ou individual(is)\n'
    text += '/flex f1graph [[user1] [user2] ..] - plot do ranking, geral ou individual(is), por dia\n'
    text += '/flex f1graph2 [[user1] [user2] ..] - plot do ranking, geral ou individual(is), por entradas\n'
    text += '/flex hour [[user1] [user2] ..] - heatmap do horário das flexões, geral ou individual(is)\n'
    text += '/flex [today|day|hoje] [[user1] [user2] ..] - gráfico de barras de hoje\n'
    text += '/flex [yesterday|ontem] [[user1] [user2] ..] - gráfico de barras de ontem\n'
    text += '/flex [daybeforeyesterday|anteontem] [[user1] [user2] ..] - gráfico de barras de anteontem\n'
    text += '/flex [daybeforedaybeforeyesterday|anteanteontem] [[user1] [user2] ..] - gráfico de barras de anteanteontem\n'
    text += '/flex [week|semana] [[user1] [user2] ..] - gráfico de barras da semana\n'
    text += '/flex [month|mes] [[user1] [user2] ..] - gráfico de barras do mês\n'
    text += '/flex top[1|2|3]day - gráfico dos top N de cada dia\n'
    return text


def send_graph(update, context):
    if update.message.text == '/flex':
        generate_flex_graph_all()
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('all.png', 'rb'))
    else:
        user = update.message.text.split('/flex ')[1]
        if ' ' in user:
            user_list = lower_list(user.split(' '))
            user = user_list[0]
        else:
            user_list = None
        if user in ['nanica', 'prata', 'nanicaprata', 'pratananica']:
            send_standings(update, context, user)
        elif user == 'gui' or user == 'guicane':
            context.bot.send_photo(chat_id=update.message.chat_id, caption='I only do legs', photo=open(f'legs.png', 'rb'))
        elif user in ['today', 'day', 'hoje', 'yesterday', 'ontem',
                        'daybeforeyesterday', 'thedaybeforeyesterday', 'anteontem',
                        'daybeforedaybeforeyesterday', 'thedaybeforethedaybeforeyesterday', 'anteanteontem',
                        'week', 'semana', 'month', 'mes']:
            generate_period(user, user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'period.png', 'rb'))
        elif user == 'accum':
            generate_accum_graph(user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'accum.png', 'rb'))
        elif user == 'accum2':
            generate_accum2_graph(user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'accum2.png', 'rb'))
        elif user == 'accum100':
            generate_accum100_graph(user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'accum100.png', 'rb'))
        elif user == 'f1graph':
            generate_f1_graph(user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'f1graph.png', 'rb'))
        elif user == 'f1graph2':
            generate_f1_graph2(user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'f1graph2.png', 'rb'))
        elif user == 'hour':
            generate_hour_graph(user_list)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open('hourgraph.png', 'rb'))
        elif user == 'top1day':
            generate_top_day_flex(1)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open('topday.png', 'rb'))
        elif user == 'top2day':
            generate_top_day_flex(2)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open('topday.png', 'rb'))
        elif user == 'top3day':
            generate_top_day_flex(3)
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open('topday.png', 'rb'))
        elif user == 'help':
            text = generate_help_message()
            context.bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            if user_list is not None:
                image_name = generate_flex_graphs(user_list)
                context.bot.send_photo(chat_id=update.message.chat_id, photo=open(image_name, 'rb'))
            else:
                generate_flex_graph_split(user)
                context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'{user}.png', 'rb'))


def send_standings(update, context, banana):
    generate_standings(banana)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f'{banana}.png', 'rb'))


def send_prata(update, context):
    send_standings(update, context, 'prata')


def send_nanica(update, context):
    send_standings(update, context, 'nanica')

def send_pratananica(update, context):
    send_standings(update, context, 'pratananica')


def increase_sentada(result):
    data = result
    seen = list()
    new_data = list()
    sentada = int(0)
    for i in data:
        if i['date'] in seen:
            sentada += 1
            i['set'] = sentada
        else:
            sentada = 1
            i['set'] = sentada
            seen.append(i['date'])
        new_data.append(i)
    return new_data






def flex_menu(update, context):
    if update.message.text.startswith('/flex'):
        search = update.message.text.split('/beer ')[1]
        beers = search_untappd(search)
    elif update.message.text.startswith('/homebrew'):
        search = update.message.text.split('/homebrew ')[1]
        beers = search_untappd(search, homebrew=True)
    buttons = list()
    for b in beers:
        emoji = emojify(b['country'])
        buttons.append(InlineKeyboardButton(f'{emoji}  {b["name"]} by {b["brewery"]} - ({b["checkin_count"]}) checkins',
                                            callback_data=f'beer,{b["bid"]}'))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
    update.message.reply_text('Which one do you mean?', reply_markup=reply_markup)


# generate_flex_graph_all()
# progression('nanica')
# generate_flex_graph('lalo')
# generate_prata_standings()
# generate_standings('nanica')
# a = get_flex_day_split('bruno')
# for i in a:
#     print(i)
# print('================')
# b = increase_sentada(a)
# for i in b:
#     print(i)
# generate_flex_graph_split('caue')
# a = progression('nanica')
# print(a)
# generate_period('month')
# generate_standings('prata')
