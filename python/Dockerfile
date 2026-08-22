FROM python:3.12-slim

# coreutils (head/od) und gawk (awk) fuer die Datei-Inspektion (Roh-CSV/XML)
RUN apt-get update \
    && apt-get install -y --no-install-recommends coreutils gawk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /dbt_project

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Kein ENTRYPOINT: Teilnehmende rufen die Werkbank mit
#   docker compose run --rm workbench <befehl>
# auf (z.B. python /work/load_raw.py oder dbt build).
CMD ["bash"]
