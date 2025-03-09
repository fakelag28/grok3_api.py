import base64
import json
import logging
import os
import sys
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, List, Optional
import requests
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEW_CHAT_URL = "https://grok.com/rest/app-chat/conversations/new"
UPLOAD_FILE_URL = "https://grok.com/rest/app-chat/upload-file"
GROK3_MODEL_NAME = "grok-3"
GROK3_REASONING_MODEL_NAME = "grok-3-reasoning"
COMPLETIONS_PATH = "/v1/chat/completions"
LIST_MODELS_PATH = "/v1/models"
MESSAGE_CHAR_LIMIT = 40000
DEFAULT_BEFORE_PROMPT_TEXT = (
    "For the data below, entries with 'system' are system information, "
    "entries with 'assistant' are messages you have previously sent, "
    "entries with 'user' are messages sent by the user. You need to respond "
    "to the user's last message accordingly based on the corresponding data."
)

api_token = None
grok_cookies = []
text_before_prompt = DEFAULT_BEFORE_PROMPT_TEXT
text_after_prompt = ""
keep_chat = False
ignore_thinking = False
http_proxy = None
next_cookie_index = {"index": 0, "lock": threading.Lock()}


class GrokClient:
    def __init__(self, cookie: str, is_reasoning: bool, enable_search: bool,
                 upload_message: bool, keep_chat: bool, ignore_thinking: bool):
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://grok.com",
            "priority": "u=1, i",
            "referer": "https://grok.com/",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            "cookie": cookie,
        }
        self.is_reasoning = is_reasoning
        self.enable_search = enable_search
        self.upload_message = upload_message
        self.keep_chat = keep_chat
        self.ignore_thinking = ignore_thinking
        self.session = requests.Session()
        self.session.timeout = 30 * 60
        if http_proxy:
            self.session.proxies = {"http": http_proxy, "https": http_proxy}

    def prepare_payload(self, message: str, file_id: str) -> Dict[str, Any]:
        tool_overrides = {"imageGen": False, "trendsSearch": False, "webSearch": False,
                         "xMediaSearch": False, "xPostAnalyze": False, "xSearch": False}
        if self.enable_search:
            tool_overrides = {}

        file_attachments = [file_id] if file_id else []

        return {
            "deepsearchPreset": "",
            "disableSearch": False,
            "enableImageGeneration": True,
            "enableImageStreaming": True,
            "enableSideBySide": True,
            "fileAttachments": file_attachments,
            "forceConcise": False,
            "imageAttachments": [],
            "imageGenerationCount": 2,
            "isPreset": False,
            "isReasoning": self.is_reasoning,
            "message": message,
            "modelName": "grok-3",
            "returnImageBytes": False,
            "returnRawGrokInXaiRequest": False,
            "sendFinalMetadata": True,
            "temporary": not self.keep_chat,
            "toolOverrides": tool_overrides,
            "webpageUrls": [],
        }

    def get_model_name(self) -> str:
        return GROK3_REASONING_MODEL_NAME if self.is_reasoning else GROK3_MODEL_NAME

    def do_request(self, method: str, url: str, payload: Dict[str, Any]) -> requests.Response:
        response = self.session.request(method, url, json=payload, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"the Grok API error: {response.status_code} {response.reason}, "
                           f"response body: {response.text}")
        return response

    def upload_message_as_file(self, message: str) -> Dict[str, str]:
        content = base64.b64encode(message.encode()).decode()
        payload = {
            "content": content,
            "fileMimeType": "text/plain",
            "fileName": f"{uuid.uuid4()}.txt",
        }
        logger.info("Uploading the message as a file")
        response = self.do_request("POST", UPLOAD_FILE_URL, payload)
        result = response.json()
        if not result.get("fileMetadataId"):
            raise Exception("uploading file error: empty `fileMetadataId`")
        return result

    def send_message(self, message: str, stream: bool) -> requests.Response:
        file_id = ""
        if self.upload_message or len(message) > MESSAGE_CHAR_LIMIT:
            upload_resp = self.upload_message_as_file(message)
            file_id = upload_resp["fileMetadataId"]
            message = "Follow the instructions in the attached file to respond."

        payload = self.prepare_payload(message, file_id)
        return self.do_request("POST", NEW_CHAT_URL, payload)


def parse_grok3_streaming_json(response: requests.Response, handler: callable, ignore_thinking: bool):
    is_thinking = False
    for line in response.iter_lines():
        if line:
            token = json.loads(line.decode())
            resp_token = token["result"]["response"]["token"]
            if ignore_thinking and token["result"]["response"]["isThinking"]:
                continue
            elif token["result"]["response"]["isThinking"]:
                if not is_thinking:
                    resp_token = "<think>\n" + resp_token
                is_thinking = True
            elif is_thinking:
                resp_token = resp_token + "\n</think>\n\n"
                is_thinking = False

            if resp_token:
                handler(resp_token)


def create_openai_streaming_response(grok_client: GrokClient, response: requests.Response, w: BaseHTTPRequestHandler):
    w.send_response(200)
    w.send_header("Content-Type", "text/event-stream")
    w.send_header("Cache-Control", "no-cache")
    w.send_header("Connection", "keep-alive")
    w.end_headers()

    completion_id = f"chatcmpl-{uuid.uuid4()}"
    start_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": grok_client.get_model_name(),
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": ""}],
    }
    w.wfile.write(f"data: {json.dumps(start_chunk)}\n\n".encode())
    w.wfile.flush()

    def handler(resp_token: str):
        chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": grok_client.get_model_name(),
            "choices": [{"index": 0, "delta": {"content": resp_token}, "finish_reason": ""}],
        }
        w.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
        w.wfile.flush()

    parse_grok3_streaming_json(response, handler, grok_client.ignore_thinking)

    final_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": grok_client.get_model_name(),
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    w.wfile.write(f"data: {json.dumps(final_chunk)}\n\n".encode())
    w.wfile.write(b"data: [DONE]\n\n")
    w.wfile.flush()


def create_openai_full_response(grok_client: GrokClient, response: requests.Response) -> Dict[str, Any]:
    full_response = []
    parse_grok3_streaming_json(response, lambda token: full_response.append(token), grok_client.ignore_thinking)
    content = "".join(full_response)
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": grok_client.get_model_name(),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": -1, "completion_tokens": -1, "total_tokens": -1},
    }


def get_cookie_index(length: int, cookie_index: int) -> int:
    if cookie_index == 0 or cookie_index > length:
        with next_cookie_index["lock"]:
            index = next_cookie_index["index"]
            next_cookie_index["index"] = (next_cookie_index["index"] + 1) % length
            return index % length
    return cookie_index - 1


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != COMPLETIONS_PATH:
            self.send_error(404, "Requested Path Not Found")
            return

        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            self.send_error(401, "Unauthorized: Bearer token required")
            return

        token = auth_header[len("Bearer "):].strip()
        if token != api_token:
            self.send_error(401, "Unauthorized: Invalid token")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length).decode())

        cookie, cookie_index = "", 0
        if "grokCookies" in body:
            if isinstance(body["grokCookies"], str):
                cookie = body["grokCookies"].strip()
            elif isinstance(body["grokCookies"], list) and body["grokCookies"]:
                cookie_index = get_cookie_index(len(body["grokCookies"]), body.get("cookieIndex", 0))
                cookie = body["grokCookies"][cookie_index].strip()
        if not cookie and grok_cookies:
            cookie_index = get_cookie_index(len(grok_cookies), body.get("cookieIndex", 0))
            cookie = grok_cookies[cookie_index]
        if not cookie:
            self.send_error(400, "Error: No Grok 3 cookie")
            return

        if not body.get("messages"):
            self.send_error(400, "Bad Request: No messages provided")
            return

        before_prompt = body.get("textBeforePrompt", text_before_prompt)
        after_prompt = body.get("textAfterPrompt", text_after_prompt)

        message_builder = [before_prompt]
        for msg in body["messages"]:
            message_builder.append(f"\n[[{msg['role']}]]\n{msg['content']}")
        message_builder.append(f"\n{after_prompt}")
        message = "".join(message_builder)

        is_reasoning = body.get("model", "").strip() == GROK3_REASONING_MODEL_NAME
        enable_search = body.get("enableSearch", -1) > 0
        upload_message = body.get("uploadMessage", -1) > 0
        keep_conversation = body.get("keepChat", -1) > 0 if body.get("keepChat", -1) >= 0 else keep_chat
        ignore_think = body.get("ignoreThinking", -1) > 0 if body.get("ignoreThinking", -1) >= 0 else ignore_thinking

        grok_client = GrokClient(cookie, is_reasoning, enable_search, upload_message,
                                keep_conversation, ignore_think)
        logger.info(f"Use the cookie with index {cookie_index + 1} to request Grok 3 Web API")

        try:
            response = grok_client.send_message(message, body.get("stream", False))
            if body.get("stream", False):
                create_openai_streaming_response(grok_client, response, self)
            else:
                full_response = create_openai_full_response(grok_client, response)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(full_response).encode())
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")

    def do_GET(self):
        if self.path != LIST_MODELS_PATH:
            self.send_error(404, "Requested Path Not Found")
            return

        model_list = {
            "object": "list",
            "data": [
                {"id": GROK3_MODEL_NAME, "object": "model", "owned_by": "xAI"},
                {"id": GROK3_REASONING_MODEL_NAME, "object": "model", "owned_by": "xAI"},
            ],
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(model_list).encode())


def main():
    global api_token, grok_cookies, text_before_prompt, text_after_prompt
    global keep_chat, ignore_thinking, http_proxy

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default="", help="Authentication token (GROK3_AUTH_TOKEN)")
    parser.add_argument("--cookie", default="", help="Grok cookie (GROK3_COOKIE)")
    parser.add_argument("--textBeforePrompt", default=DEFAULT_BEFORE_PROMPT_TEXT,
                       help="Text before the prompt")
    parser.add_argument("--textAfterPrompt", default="", help="Text after the prompt")
    parser.add_argument("--keepChat", action="store_true", help="Retain the chat conversation")
    parser.add_argument("--ignoreThinking", action="store_true",
                       help="Ignore the thinking content while using the reasoning model")
    parser.add_argument("--httpProxy", default="", help="HTTP/SOCKS5 proxy")
    parser.add_argument("--port", type=int, default=8180, help="Server port")
    args = parser.parse_args()

    if args.port > 65535:
        logger.fatal(f"Server port {args.port} is greater than 65535")
        sys.exit(1)

    api_token = args.token.strip() or os.getenv("GROK3_AUTH_TOKEN", "")
    if not api_token:
        logger.fatal("Authentication token (GROK3_AUTH_TOKEN) is unset")
        sys.exit(1)

    cookie = args.cookie.strip() or os.getenv("GROK3_COOKIE", "")
    if cookie:
        try:
            grok_cookies = json.loads(cookie)
            if not isinstance(grok_cookies, list):
                grok_cookies = [cookie]
        except json.JSONDecodeError:
            grok_cookies = [cookie]

    text_before_prompt = args.textBeforePrompt
    text_after_prompt = args.textAfterPrompt
    keep_chat = args.keepChat
    ignore_thinking = args.ignoreThinking
    http_proxy = args.httpProxy.strip()

    server = ThreadingHTTPServer(("0.0.0.0", args.port), RequestHandler)
    logger.info(f"Server starting on :{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()