# Use an official Python runtime as a parent image
FROM python:3.5-slim

# Set the working directory to /app
WORKDIR /Elascale_secure

# Copy the current directory contents into the container at /app
ADD . /Elascale_secure

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Change directory
WORKDIR /Elascale_secure/mape

# Run app.py when the container launches
CMD ["python3", "analyze.py"]
