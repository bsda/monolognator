FROM python:3.8 as base

FROM base as builder

RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM python:3.8-alpine

COPY --from=builder /install /usr/local
WORKDIR /
ADD bot.py /
ADD beer.py /
ADD gif.py /
ADD monologue.py /
ADD weather.py /
ADD config.py /
ADD entry.sh /
RUN apk add openssl bash
#RUN pip install pip --upgrade
RUN chmod +x /entry.sh
CMD /entry.sh
