# Använd en officiell Python-bild som bas
FROM python:3.9-slim

# Sätt arbetskatalogen i containern
WORKDIR /app

# Kopiera requirements.txt till containern
COPY requirements.txt /app/

# Installera Python-bibliotek från requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera applikationen till containern
COPY app.py /app/

# Exponera porten som Flask använder
EXPOSE 5000

# Kör applikationen med Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
