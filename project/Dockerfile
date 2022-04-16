FROM python:3.8-alpine
EXPOSE 3111

RUN pip install --upgrade pip

RUN adduser -D app
ENV PATH="/home/app/.local/bin:${PATH}"

USER app
WORKDIR /home/app

LABEL maintainer="Marius Tanawa Tsamo"

COPY --chown=app:app ./techtrends/requirements.txt requirements.txt
RUN pip install --user -r requirements.txt



COPY --chown=app:app ./techtrends .

CMD python init_db.py && python app.py
