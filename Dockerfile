FROM ubuntu:latest

RUN apt-get update && apt-get upgrade -y && apt-get install -y cron python3 python3-pip libpq-dev

ADD ./cron/crontab /etc/cron.d/simple-cron

WORKDIR /app

COPY . .

RUN chmod 0644 /etc/cron.d/simple-cron && pip3 install -r reg.txt && \
touch /var/log/cron.log && chmod +x /app/cron/script.sh

# Run the command on container startup
ENTRYPOINT ["cron", "-f"]