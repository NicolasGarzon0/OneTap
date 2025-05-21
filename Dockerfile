# 1. Use an official Python base image
FROM python:3.12-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Copy only necessary files first (for faster caching)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code
COPY . .

# 6. Expose the app port
EXPOSE 8000

# 7. Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
