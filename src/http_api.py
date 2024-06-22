import requests
import logging
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class HttpClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        # Set up logging
        logging.basicConfig(
            filename="http_client.log",
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def log_request(self, method, url, data, response=None, error=None):
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{time_str} - {method} - {url} - Data: {data} - Response: {response} - Error: {error}"

        # Log to file
        logging.info(log_message)

        # Log to CLI with colors
        time_colored = f"{Fore.GREEN}{time_str}{Style.RESET_ALL}"
        method_colored = f"{Fore.CYAN}{method}{Style.RESET_ALL}"
        url_colored = f"{Fore.YELLOW}{url}{Style.RESET_ALL}"
        data_colored = f"{Fore.MAGENTA}{data}{Style.RESET_ALL}"
        response_colored = f"{Fore.BLUE}{response}{Style.RESET_ALL}"
        error_colored = f"{Fore.RED}{error}{Style.RESET_ALL}" if error else ""

        cli_message = f"{time_colored} - {method_colored} - {url_colored} - Data: {data_colored} - Response: {response_colored}"
        if error:
            cli_message += f" - Error: {error_colored}"
        print(cli_message)

    def post(self, url, data):
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response_json = response.json()
            self.log_request("POST", url, data, response_json)
            return response_json
        except Exception as e:
            self.log_request("POST", url, data, error=str(e))
            print(f"Error occurred during API call: {str(e)}")
            return None

    def get(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response_json = response.json()
            self.log_request("GET", url, None, response_json)
            return response_json
        except Exception as e:
            self.log_request("GET", url, None, error=str(e))
            print(f"Error occurred during API call: {str(e)}")
            return None


class ChatAPIService:
    def __init__(self, api_key, model_name="gpt-4o", temperature=1.0):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.http_client = HttpClient(api_key)

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
