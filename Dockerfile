FROM python:3.8

RUN pip install --upgrade pip

WORKDIR /algoproject
ADD requirements.txt .
RUN pip install -r requirements.txt

ADD start.sh ./
RUN sed -i 's/\r$//' start.sh
RUN chmod +x start.sh
ENTRYPOINT ["sh", "start.sh"]
