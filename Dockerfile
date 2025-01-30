# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download SpaCy model
RUN python -m spacy download en_core_web_md

# Expose port 80 if needed
EXPOSE 80

# Run bot.py when the container launches
CMD ["sh", "-c", "python app.py & python bot.py"]
