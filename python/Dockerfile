FROM python:3.12-slim

# coreutils (head/od) und gawk (awk) fuer die Datei-Inspektion in Uebung 1
RUN apt-get update \
    && apt-get install -y --no-install-recommends coreutils gawk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kein ENTRYPOINT: Teilnehmende rufen den Container mit
#   docker compose run --rm python <befehl>
# auf (z.B. head, od, awk oder python parser.py).
CMD ["python"]
