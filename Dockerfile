FROM python:3.8 as base

FROM base as builder

RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM python:3.8-slim

COPY --from=builder /install /usr/local
WORKDIR /app
ADD bot.py /app
ADD beer.py /app
ADD gif.py /app
ADD monologue.py /app
ADD weather.py /app
ADD config.py /app
ADD twitter.py /app
ADD corona.py /app
ADD entry.sh /app
ADD movies.py /app
ADD utils.py /app
#RUN apk update && apk add --no-cache openssl bash libstdc++ libc6-compat protobuf
RUN apt update; apt install procps --assume-yes
ENTRYPOINT [ "python3", "bot.py" ]

