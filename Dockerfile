FROM python:3 as base

FROM base as builder

RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM python:3.7-alpine
COPY --from=builder /install /usr/local
ARG cn
ENV cn=${cn}
ADD bot.py /
ADD beer.py /
ADD gif.py /
ADD monologue.py /
ADD weather.py /
RUN echo ${cn}
RUN apk add openssl
RUN openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem -subj /CN=${cn}
#RUN pip install pip --upgrade
ENTRYPOINT [ "python3", "./bot.py" ]
