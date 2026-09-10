FROM python:3.13-slim AS build

WORKDIR /site
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN sphinx-build -b dirhtml -D language=ru source _build/site \
 && sphinx-build -b dirhtml -D language=en source _build/site/en

FROM nginxinc/nginx-unprivileged:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site/_build/site /usr/share/nginx/html
EXPOSE 8080

