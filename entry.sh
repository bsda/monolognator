openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem -subj /CN=${CN}

python3 bot.py

