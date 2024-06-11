import yaml
import requests
import json
from abc import ABC, abstractmethod


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


class ChatAPIService:
    def __init__(self, api_key, model_name="gpt-4o", temperature=1.0):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.http_client = HttpClient(api_key)

    def execute_api_call(self, messages, tools):
        url = "https://openrouter.ai/api/v1/chat/completions"
        data = {
            "messages": [
                {"role": msg["role"], "content": msg["content"]} for msg in messages
            ],
            "model": self.model_name,
            "temperature": self.temperature,
            "tools": tools,
        }

        response = self.http_client.post(url, data)
        return response


class TaskExecutor:
    @staticmethod
    def execute_task(task_name, arguments):
        task = AITaskRegistry.get_command(task_name)
        if task:
            return task.execute(json.loads(arguments))
        else:
            print(f"Task '{task_name}' not found.")
            return None


class ResponseHandler:
    def __init__(self):
        self.conversation_history = []

    def handle_response(self, response):
        if "choices" in response:
            choice = response["choices"][0]
            if "message" in choice:
                self._handle_message(choice["message"])
            else:
                print(f"No message found in the response.")
        else:
            print(f"API response: {response}")

    def _handle_message(self, message):
        if "tool_calls" in message:
            self._handle_tool_calls(message["tool_calls"])
        elif "content" in message:
            self._handle_content(message["content"])
        else:
            print(f"No content or tool calls found in the message.")

    def _handle_tool_calls(self, tool_calls):
        for tool_call in tool_calls:
            task_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            result = TaskExecutor.execute_task(task_name, arguments)
            print(f"Task result: {result}")

    def _handle_content(self, content):
        self.conversation_history.append({"role": "assistant", "content": content})

    def add_user_message(self, message):
        self.conversation_history.append({"role": "user", "content": message})

    def get_conversation_history(self):
        return self.conversation_history


class ToolsLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tools = []

    def load_tools_from_yaml(self):
        with open(self.file_path, "r") as file:
            tools_data = yaml.safe_load(file)
            self.tools = tools_data["tools"]

    def load_tools(self):
        self.load_tools_from_yaml()
        self.register_tools()

    def register_tools(self):
        for tool_data in self.tools:
            tool_name = tool_data["function"]["name"]
            tool_class = self.get_tool_class(tool_name)
            AITaskRegistry.register(tool_name, tool_class())

    def get_tool_class(self, tool_name):
        tool_class_name = (
            "".join(word.capitalize() for word in tool_name.split("_")) + "Task"
        )
        return globals()[tool_class_name]


class AITaskCommand(ABC):
    @abstractmethod
    def execute(self, arguments):
        pass


class AITaskRegistry:
    _instance = None
    _registry = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, task_name, command):
        cls._registry[task_name] = command

    @classmethod
    def get_command(cls, task_name):
        return cls._registry.get(task_name)


class GoToPageTask(AITaskCommand):
    def execute(self):
        pass
