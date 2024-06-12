from abc import ABC, abstractmethod
import json
from typing import Dict, Any


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


class TaskExecutor:

    @staticmethod
    def execute_task(task_name, arguments, dependencies_container):
        task = AITaskRegistry.get_command(task_name)
        if task:
            return task.execute(json.loads(arguments), dependencies_container)
        else:
            print(f"Task '{task_name}' not found.")
            return None


class Task(ABC):
    @abstractmethod
    def execute(self, arguments, dependencies_container):
        pass


class GoToPageTask(Task):
    async def execute(self, arguments, dependencies_container):
        browser = dependencies_container.get("web_browser")
        if browser:
            await browser.navigate_to(arguments["url"])
            print("Page loaded successfully.")
            forms = await FormUtils.get_forms(browser)
            parsed_forms = FormParser.parse_forms(forms)
            formatted_response = CLIResponseFormatter().format(parsed_forms)
            print(formatted_response)


class FormElementHandler(ABC):
    @abstractmethod
    async def handle(self, element) -> Dict[str, Any]:
        pass


class InputFieldHandler(FormElementHandler):
    async def handle(self, element) -> Dict[str, Any]:
        return {
            "type": await element.get_attribute("type"),
            "name": await element.get_attribute("name"),
            "id": await element.get_attribute("id"),
            "class": await element.get_attribute("class"),
            "placeholder": await element.get_attribute("placeholder"),
            "label": await self.get_associated_label(element),
        }

    async def get_associated_label(self, element):
        label_element = await element.query_selector(
            "xpath=preceding-sibling::label[1]"
        )
        if label_element:
            return await label_element.inner_text()
        return None


class ButtonHandler(FormElementHandler):
    async def handle(self, element) -> Dict[str, Any]:
        return {
            "type": await element.get_attribute("type"),
            "name": await element.get_attribute("name"),
            "id": await element.get_attribute("id"),
            "class": await element.get_attribute("class"),
            "value": await element.get_attribute("value"),
            "label": await self.get_button_label(element),
        }

    async def get_button_label(self, button):
        if await button.get_attribute("value"):
            return await button.get_attribute("value")
        return await button.inner_text()


class SelectHandler(FormElementHandler):
    async def handle(self, element) -> Dict[str, Any]:
        return {
            "name": await element.get_attribute("name"),
            "id": await element.get_attribute("id"),
            "class": await element.get_attribute("class"),
            "label": await self.get_associated_label(element),
            "options": await self.get_select_options(element),
        }

    async def get_associated_label(self, element):
        label_element = await element.query_selector(
            "xpath=preceding-sibling::label[1]"
        )
        if label_element:
            return await label_element.inner_text()
        return None

    async def get_select_options(self, select):
        options = await select.query_selector_all("option")
        return [await option.get_attribute("value") for option in options]


element_handlers = {
    "input": InputFieldHandler(),
    "button": ButtonHandler(),
    "select": SelectHandler(),
}


class FormUtils:
    @staticmethod
    async def get_forms(browser):
        forms = []
        page = browser.page
        elements = await page.query_selector_all("form")
        for element in elements:
            form_data = {
                "id": await element.get_attribute("id"),
                "name": await element.get_attribute("name"),
                "action": await element.get_attribute("action"),
                "method": await element.get_attribute("method"),
                "elements": [],
            }

            for element_type, handler in element_handlers.items():
                sub_elements = await element.query_selector_all(element_type)
                for sub_element in sub_elements:
                    element_data = await handler.handle(sub_element)
                    form_data["elements"].append(element_data)

            forms.append(form_data)

        return forms


class FormParser:
    @staticmethod
    def parse_forms(forms):
        num_forms = len(forms)
        feedback = f"Website loaded successfully. It has {num_forms} form(s).\n\n"

        for index, form in enumerate(forms, start=1):
            form_id = form.get("id", "N/A")
            form_name = form.get("name", "N/A")
            form_action = form.get("action", "N/A")
            form_method = form.get("method", "GET")
            num_elements = len(form["elements"])

            feedback += f"Form {index}:\n"
            feedback += f"  ID: {form_id}\n"
            feedback += f"  Name: {form_name}\n"
            feedback += f"  Action: {form_action}\n"
            feedback += f"  Method: {form_method}\n"
            feedback += f"  Number of Elements: {num_elements}\n"

            feedback += "  Elements:\n"
            for element in form["elements"]:
                element_type = element.get("type", "N/A")
                element_name = element.get("name", "N/A")
                element_id = element.get("id", "N/A")
                element_class = element.get("class", "N/A")
                element_label = element.get("label", "N/A")

                feedback += f"    - Type: {element_type}\n"
                feedback += f"      Name: {element_name}\n"
                feedback += f"      ID: {element_id}\n"
                feedback += f"      Class: {element_class}\n"
                feedback += f"      Label: {element_label}\n"

                if element_type == "select":
                    options = element.get("options", [])
                    feedback += f"      Options: {', '.join(options)}\n"

            feedback += "\n"

        return feedback


class CLIResponseFormatter:
    def format(self, response):
        # Colored CLI output using ANSI escape codes
        return "\033[94m" + response + "\033[0m"


class JSONResponseFormatter:
    def format(self, response):
        import json

        return json.dumps(response, indent=2)
