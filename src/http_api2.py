import requests
import logging
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class Logger:
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            filename="http_client.log",
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def log(self, message):
        # Log to file
        logging.info(message)


class ColorLogger(Logger):
    def log(self, message, method=None, url=None, data=None, response=None, error=None):
        super().log(message)
        if any(param is not None for param in [method, url, data, response, error]):
            # Log to CLI with colors
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_colored = f"{Fore.GREEN}{time_str}{Style.RESET_ALL}"
            method_colored = f"{Fore.CYAN}{method}{Style.RESET_ALL}" if method else ""
            url_colored = f"{Fore.YELLOW}{url}{Style.RESET_ALL}" if url else ""
            data_colored = f"{Fore.MAGENTA}{data}{Style.RESET_ALL}" if data else ""
            response_colored = (
                f"{Fore.BLUE}{response}{Style.RESET_ALL}" if response else ""
            )
            error_colored = f"{Fore.RED}{error}{Style.RESET_ALL}" if error else ""

            cli_message = f"{time_colored} - {method_colored} - {url_colored} - Data: {data_colored} - Response: {response_colored}"
            if error:
                cli_message += f" - Error: {error_colored}"
            print(cli_message)


class HttpClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def post(self, url, data):
        try:
            response = requests.post(url, headers=self.headers, json=data)
            return response.json()
        except Exception as e:
            print(f"Error occurred during API call: {str(e)}")
            return None

    def get(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            print(f"Error occurred during API call: {str(e)}")
            return None


class HttpClientWithLogging(HttpClient):
    def __init__(self, api_key, logger):
        super().__init__(api_key)
        self.logger = logger

    def log_request(self, method, url, data, response=None, error=None):
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{time_str} - {method} - {url} - Data: {data} - Response: {response} - Error: {error}"
        self.logger.log(log_message, method, url, data, response, error)

    def post(self, url, data):
        response = super().post(url, data)
        self.log_request("POST", url, data, response)
        return response

    def get(self, url):
        response = super().get(url)
        self.log_request("GET", url, None, response)
        return response


class ChatAPIService:
    def __init__(self, api_key, model_name="gpt-4o", temperature=1.0):
        self.model_name = model_name
        self.temperature = temperature
        logger = ColorLogger()
        self.http_client = HttpClientWithLogging(api_key, logger)

    def execute_api_call(self, messages, **kwargs):
        url = "https://openrouter.ai/api/v1/chat/completions"
        base_data = {
            "messages": [
                {"role": msg["role"], "content": msg["content"]} for msg in messages
            ],
            "model": self.model_name,
            "temperature": self.temperature,
        }

        # Merge base_data with kwargs to include any additional parameters
        data = {**base_data, **kwargs}

        response = self.http_client.post(url, data)
        return response
