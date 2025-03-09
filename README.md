### Grok 3 Web API Wrapper (Python Version)

#### English Version

##### Overview

It is a fork of the tool (On Go) rewritten in Python, designed to interact with the Grok 3 webAPI, providing an OpenAI-compatible API endpoint for running chat comblets. It allows users to send messages to the Grok 3 webAPI and receive responses in a format compatible with the OpenAI chat combo API.
##### Features

- **OpenAI-Compatible Endpoint**: Supports `/v1/chat/completions` and `/v1/models` endpoints.
- **Streaming Support**: Enables real-time streaming of responses.
- **Model Selection**: Choose between standard and reasoning models.
- **Cookie Management**: Manages multiple cookies.
- **Proxy Support**: Compatible with HTTP and SOCKS5 proxies for network requests.
- **Configurable Options**: Includes flags for retaining chat conversations, filtering thinking content, and adding custom text to prompts.

##### Prerequisites

Before you use this tool, ensure you have the following:

- **Grok Cookie**: Obtain your account's cookie from [grok.com](https://grok.com) by your browser.
- **API Authentication Token**: Prepare a token to secure the OpenAI-compatible API endpoints.

##### Basic Usage

The API authentication token is **required** while running this tool. The Grok cookie must be set by the `-cookie` flag or the request body.

Run this:

```
grok3_api -token your_secret_token
```

Then the OpenAI-compatible API endpoints can be accessed through `http://127.0.0.1:8180/v1`.

##### Configuration

You can configure this tool using command-line flags, environment variables, or the request body.

###### Command-Line Flags

- `-token`: API authentication token (**required**).
- `-cookie`: Grok cookie(s) for authentication. Accepts a single cookie or a JSON array of cookies.
- `-textBeforePrompt`: Text to add before the user’s message. The default text can be viewed by using the `-help` flag.
- `-textAfterPrompt`: Text to add after the user’s message (default: empty string).
- `-keepChat`: Retains chat conversations after each request if set.
- `-ignoreThinking`: Excludes thinking tokens from responses when using the reasoning model.
- `-httpProxy`: Specifies an HTTP or SOCKS5 proxy URL (e.g., `http://127.0.0.1:1080` or `socks5://127.0.0.1:1080`).
- `-port`: Sets the server port (default: 8180).
- `-help`: Prints the help message.

###### Environment Variables

- `GROK3_AUTH_TOKEN`: Alternative to the `-token` flag.
- `GROK3_COOKIE`: Alternative to the `-cookie` flag.
- `http_proxy`: Alternative to the `-httpProxy` flag.

###### Request Body for Completion

Some configurations can be set in the request body while using the `/v1/chat/completions` endpoint.

Request body (JSON):

```json
{
  "messages": [],
  "model": "grok-3", // "grok-3" for the standard Grok 3 model, "grok-3-reasoning" for the Grok 3 reasoning model.
  "stream": true, // true for streaming response.
  "grokCookies": ["cookie1", "cookie2"], // a string for a single cookie, or a list of strings for multiple cookies.
  "cookieIndex": 1, // the index of cookie (starting from 1) to request Grok 3 Web API. If the index is 0, auto-selecting cookies in turn (default behaviour).
  "enableSearch": 1, // 1 to enable web searching, 0 to disable (default behaviour).
  "uploadMessage": 1, // 1 to upload the message as a file (for very long messages), 0 to upload only if the character count exceeds 40,000 (default behaviour).
  "textBeforePrompt": "System: You are a helpful assistant.", // text to add before the user’s message.
  "textAfterPrompt": "End of message.", // text to add after the user’s message (default: empty string).
  "keepChat": 1, // 1 to retain this chat conversation, 0 to not retain it (default behaviour).
  "ignoreThinking": 1 // 1 to exclude thinking tokens from the response when using the reasoning model, 0 to retain thinking tokens (default behaviour).
}
```

##### Warnings

This tool offers an unofficial OpenAI-compatible API for Grok 3, so your account may be **banned** by xAI if using this tool. Please do not abuse or use this tool for commercial purposes. Use it at your own risk.

##### Special Thanks

- [mem0ai/grok3-api: Unofficial Grok 3 API](https://github.com/mem0ai/grok3-api)
- [RoCry/grok3-api-cf: Grok 3 via API with Cloudflare for free](https://github.com/RoCry/grok3-api-cf/tree/master)

##### License

This project is licensed under the `AGPL-3.0` License.

---

#### Русская версия

##### Обзор

Это форк инструмента (На Go) переписанный под Python, разработанный для взаимодействия с веб-API Grok 3, предоставляющий API-эндпоинт, совместимый с OpenAI, для выполнения чат-комплетов. Он позволяет пользователям отправлять сообщения в веб-API Grok 3 и получать ответы в формате, совместимом с API чат-комплетов OpenAI.

##### Возможности

- **Совместимый с OpenAI эндпоинт**: Поддерживает эндпоинты `/v1/chat/completions` и `/v1/models`.
- **Поддержка потоковой передачи**: Позволяет получать ответы в режиме реального времени.
- **Выбор модели**: Возможность выбора между стандартной и рассуждающей моделью.
- **Управление cookies**: Поддерживает работу с несколькими cookies.
- **Поддержка прокси**: Совместим с HTTP и SOCKS5 прокси для сетевых запросов.
- **Настраиваемые параметры**: Включает флаги для сохранения истории чата, фильтрации содержимого рассуждений и добавления пользовательского текста в запросы.

##### Предварительные требования

Перед использованием инструмента убедитесь, что у вас есть следующее:

- **Cookie Grok**: Получите cookie вашего аккаунта с сайта [grok.com](https://grok.com) через ваш браузер.
- **Токен аутентификации API**: Подготовьте токен для защиты API-эндпоинтов, совместимых с OpenAI.

##### Базовое использование

Токен аутентификации API **обязателен** при запуске этого инструмента. Cookie Grok должен быть установлен с помощью флага `-cookie` или через тело запроса.

Запустите следующую команду:

```
grok3_api -token ваш_секретный_токен
```

После этого API-эндпоинты, совместимые с OpenAI, будут доступны через `http://127.0.0.1:8180/v1`.

##### Конфигурация

Вы можете настроить этот инструмент с помощью флагов командной строки, переменных окружения или тела запроса.

###### Флаги командной строки

- `-token`: Токен аутентификации API (**обязателен**).
- `-cookie`: Cookie Grok для аутентификации. Принимает один cookie или JSON-массив cookies.
- `-textBeforePrompt`: Текст, добавляемый перед сообщением пользователя. Значение по умолчанию можно посмотреть с помощью флага `-help`.
- `-textAfterPrompt`: Текст, добавляемый после сообщения пользователя (по умолчанию: пустая строка).
- `-keepChat`: Сохраняет историю чата после каждого запроса, если установлен.
- `-ignoreThinking`: Исключает токены рассуждений из ответов при использовании рассуждающей модели.
- `-httpProxy`: Указывает URL HTTP или SOCKS5 прокси (например, `http://127.0.0.1:1080` или `socks5://127.0.0.1:1080`).
- `-port`: Устанавливает порт сервера (по умолчанию: 8180).
- `-help`: Выводит справочное сообщение.

###### Переменные окружения

- `GROK3_AUTH_TOKEN`: Альтернатива флагу `-token`.
- `GROK3_COOKIE`: Альтернатива флагу `-cookie`.
- `http_proxy`: Альтернатива флагу `-httpProxy`.

###### Тело запроса для выполнения

Некоторые конфигурации можно указать в теле запроса при использовании эндпоинта `/v1/chat/completions`.

Тело запроса (JSON):

```json
{
  "messages": [],
  "model": "grok-3", // "grok-3" для стандартной модели Grok 3, "grok-3-reasoning" для рассуждающей модели Grok 3.
  "stream": true, // true для потокового ответа.
  "grokCookies": ["cookie1", "cookie2"], // строка для одного cookie или список строк для нескольких cookies.
  "cookieIndex": 1, // индекс cookie (начиная с 1) для запроса к веб-API Grok 3. Если индекс равен 0, cookies выбираются по очереди автоматически (поведение по умолчанию).
  "enableSearch": 1, // 1 для включения веб-поиска, 0 для отключения (поведение по умолчанию).
  "uploadMessage": 1, // 1 для загрузки сообщения как файла (для очень длинных сообщений), 0 для загрузки сообщения только если количество символов превышает 40,000 (поведение по умолчанию).
  "textBeforePrompt": "System: Вы полезный ассистент.", // текст, добавляемый перед сообщением пользователя.
  "textAfterPrompt": "Конец сообщения.", // текст, добавляемый после сообщения пользователя (по умолчанию: пустая строка).
  "keepChat": 1, // 1 для сохранения истории этого чата, 0 для несохранения (поведение по умолчанию).
  "ignoreThinking": 1 // 1 для исключения токенов рассуждений из ответа при использовании рассуждающей модели, 0 для сохранения токенов рассуждений (поведение по умолчанию).
}
```

##### Предупреждения

Этот инструмент предоставляет неофициальный API, совместимый с OpenAI, для Grok 3, поэтому ваш аккаунт может быть **заблокирован** компанией xAI при использовании этого инструмента. Пожалуйста, не злоупотребляйте этим инструментом и не используйте его в коммерческих целях. Используйте на свой страх и риск.

##### Благодарности

- [mem0ai/grok3-api: Неофициальный API Grok 3](https://github.com/mem0ai/grok3-api)
- [RoCry/grok3-api-cf: Grok 3 через API с Cloudflare бесплатно](https://github.com/RoCry/grok3-api-cf/tree/master)

##### Лицензия

Этот проект лицензирован под лицензией `AGPL-3.0`.