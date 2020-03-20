import imdb

ia = imdb.IMDb()


def search(movie):
    movies = ia.search_movie(movie)
    return movies

def movie(id):
    movie_detail = ia.get_movie(id)
    return movie_detail





m = movie('6751668')
# m=movie('2904670')
d = m.data['directors']
directors = [i.data.get('name') for i in m.data['directors']]
cast = [i.data.get('name') for i in m.data['cast'][:3]]
countries = [i for i in m.data['countries']]
air_date = m.data.get('original air date')
rating = m.data.get('rating')
cover = m.data.get('cover url')
plot = m.data.get('plot')
# budget = m.data.get('box office').get('Budget')
# gross = m.data.get('box office').get('Cumulative Worldwide Gross')





