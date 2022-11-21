# first stage
FROM python:2.7 AS builder
COPY requirements.txt .

# install dependencies to the local user directory (eg. /root/.local)
RUN pip install --user -r requirements.txt

# second unnamed stage
FROM python:2.7
WORKDIR /code

# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY ./ .

# update PATH environment variable
ENV PATH=/root/.local:$PATH

CMD ["python", "multisearcher.py", "-f", "words.txt", "-t", "10"]