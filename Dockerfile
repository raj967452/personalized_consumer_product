# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable to run in production mode
ENV FLASK_ENV=production

# Run app.py when the container launches
# Use gunicorn for a production-ready server
RUN pip install gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.app:app"]
