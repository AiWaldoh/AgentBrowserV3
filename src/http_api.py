import requests
import logging
from datetime import datetime
from colorama import Fore, Style, init
import json

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

    def color_json(self, json_str):
        try:
            parsed = json.loads(json_str)
            formatted = json.dumps(parsed, indent=2)
            colored = ""
            indent = 0
            for line in formatted.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    colored += (
                        "  " * indent
                        + f"{Fore.CYAN}{key}{Fore.RESET}:{Fore.YELLOW}{value}{Fore.RESET}\n"
                    )
                elif "{" in line or "[" in line:
                    colored += f"{Fore.MAGENTA}{line}{Fore.RESET}\n"
                    indent += 1
                elif "}" in line or "]" in line:
                    indent -= 1
                    colored += f"{Fore.MAGENTA}{line}{Fore.RESET}\n"
                else:
                    colored += f"{Fore.YELLOW}{line}{Fore.RESET}\n"
            return colored.rstrip()
        except json.JSONDecodeError:
            return f"{Fore.RED}Invalid JSON{Fore.RESET}"

    def log_request(self, method, url, data, response=None, error=None):
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log to file (commented out)
        # log_message = f"{time_str} - {method} - {url} - Data: {data} - Response: {response} - Error: {error}"
        # logging.info(log_message)

        # Log to CLI with colors
        time_colored = f"{Fore.GREEN}{time_str}{Style.RESET_ALL}"
        method_colored = f"{Fore.CYAN}{method}{Style.RESET_ALL}"
        url_colored = f"{Fore.YELLOW}{url}{Style.RESET_ALL}"

        data_colored = self.color_json(json.dumps(data)) if data else ""
        response_colored = self.color_json(json.dumps(response)) if response else ""
        error_colored = f"{Fore.RED}{error}{Style.RESET_ALL}" if error else ""

        cli_message = f"{time_colored} - {method_colored} - {url_colored}\n"
        cli_message += f"Data:\n{data_colored}\n" if data else ""
        cli_message += f"Response:\n{response_colored}\n" if response else ""
        cli_message += f"Error: {error_colored}" if error else ""

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
