FROM python:3.12-alpine
RUN apk add --no-cache bind-tools
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
