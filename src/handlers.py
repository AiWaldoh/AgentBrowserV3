from abc import ABC, abstractmethod
from typing import Dict, Any


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
            "xpath=ancestor::label | following-sibling::label | preceding-sibling::label"
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
        # await page.wait_for_selector("form", state="hidden")
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
