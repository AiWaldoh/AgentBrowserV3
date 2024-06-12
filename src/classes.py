import yaml
import requests
import json
from abc import ABC, abstractmethod
from playwright.async_api import Page, ElementHandle
from typing import List
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from tasks import TaskExecutor, AITaskRegistry, GoToPageTask


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


class MessageHandler:
    def __init__(self, successor=None):
        self._successor = successor

    async def handle(self, message, dependencies_container):
        if self._can_handle(message):
            await self._handle(message, dependencies_container)
        elif self._successor:
            await self._successor.handle(message, dependencies_container)

    def _can_handle(self, message):
        raise NotImplementedError

    async def _handle(self, message, dependencies_container):
        raise NotImplementedError


class ToolCallMessageHandler(MessageHandler):
    def _can_handle(self, message):
        return "tool_calls" in message

    async def _handle(self, message, dependencies_container):
        for tool_call in message["tool_calls"]:
            task_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            result = await TaskExecutor.execute_task(
                task_name, arguments, dependencies_container
            )
            print(f"Task result: {result}")


class ContentMessageHandler(MessageHandler):
    def __init__(self, conversation_history, successor=None):
        super().__init__(successor)
        self._conversation_history = conversation_history

    def _can_handle(self, message):
        return "content" in message

    async def _handle(self, message, dependencies_container):
        self._conversation_history.append(
            {"role": "assistant", "content": message["content"]}
        )


class TaskExecutorStrategy:
    async def execute(self, task_name, arguments, dependencies_container):
        raise NotImplementedError


class DefaultTaskExecutor(TaskExecutorStrategy):
    async def execute(self, task_name, arguments, dependencies_container):
        # Default task execution logic
        return await TaskExecutor.execute_task(
            task_name, arguments, dependencies_container
        )


class BaseResponseHandler:
    def __init__(self, dependencies_container, executor_strategy=None):
        self._conversation_history = []
        self._dependencies_container = dependencies_container
        self._executor_strategy = (
            executor_strategy if executor_strategy else DefaultTaskExecutor()
        )
        self._build_chain()

    def _build_chain(self):
        self.chain = ToolCallMessageHandler(
            successor=ContentMessageHandler(
                conversation_history=self._conversation_history
            )
        )

    async def handle_response(self, response):
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "message" in choice:
                await self.chain.handle(choice["message"], self._dependencies_container)
            else:
                print(f"No message found in the response.")
        else:
            print(f"API response: {response}")

    def add_user_message(self, message):
        self._conversation_history.append({"role": "user", "content": message})

    def get_conversation_history(self):
        return self._conversation_history


# Usage example (this part should be run in an appropriate async environment)
# dependencies_container = ...  # initialize your dependencies
# response_handler = BaseResponseHandler(dependencies_container)
# await response_handler.handle_response(response_from_api)


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


class WebBrowser:
    def __init__(self):
        self.browser = None
        self.page = None

    async def launch(self, headless=True):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)

    async def close(self):
        if self.browser:
            await self.browser.close()

    async def click_and_wait_for_network_activity(self, selector, timeout=5000):
        pending_requests = 0

        async def request_handler(route, request):
            nonlocal pending_requests
            pending_requests += 1
            print(f"Request: {request.method} {request.url}")
            await route.continue_()

        async def response_handler(response):
            nonlocal pending_requests
            print(f"Response: {response.status} {response.url}")
            if response.status == 200 and response.request.method != "OPTIONS":
                pending_requests -= 1
                print(f"Pending requests: {pending_requests}")
                if pending_requests == 0:
                    await self.page.evaluate("window.networkActivityComplete = true")

        await self.page.route("**/*", request_handler)
        self.page.on("response", response_handler)

        await self.page.evaluate("window.networkActivityComplete = false")
        await self.page.click(selector)

        try:
            await self.page.wait_for_function(
                "window.networkActivityComplete === true", timeout=timeout
            )
            return True
        except PlaywrightTimeoutError:
            print("Timeout occurred")
            return False
        finally:
            await self.page.unroute("**/*", request_handler)
            self.page.remove_listener("response", response_handler)

    async def navigate_to(self, url, timeout=30000):
        self.page = await self.browser.new_page()
        try:
            await self.page.goto(url, timeout=timeout)
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out waiting for navigation to '{url}'.")

        print(f"Page loaded: {url}")

    async def click_element(self, selector, timeout=5000):
        try:
            await self.page.click(selector, timeout=timeout)
        except PlaywrightTimeoutError:
            raise TimeoutError(
                f"Timed out waiting for element '{selector}' to be clickable"
            )

    async def fill_input(self, selector: str, value: str, delay: int = 100):
        await self.page.type(selector, value, delay=delay)

    async def get_text(self, selector: str) -> str:
        return await self.page.inner_text(selector)

    async def take_screenshot(self, file_path: str):
        await self.page.screenshot(path=file_path)

    async def wait_for_selector(self, selector: str, timeout: int = 5000):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out waiting for selector '{selector}'")

    async def wait_for_navigation(self, page: Page = None, timeout: int = 30000):
        if page is None:
            page = self.page
        await page.wait_for_load_state("networkidle", timeout=timeout)

    async def find_elements(self, selector: str) -> List[ElementHandle]:
        return await self.page.query_selector_all(selector)

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def close(self):
        await self.browser.close()


class NavigationError(Exception):
    pass


class ElementNotFoundError(Exception):
    pass


class InteractionError(Exception):
    pass
