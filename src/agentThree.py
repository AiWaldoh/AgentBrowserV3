import os
import json
from dotenv import load_dotenv
from http_api import ChatAPIService

load_dotenv()


class EnvironmentLoader:
    @staticmethod
    def load_variable(key):
        return os.getenv(key)


class FormLoader:
    @staticmethod
    def load_forms(file_path):
        with open(file_path) as file:
            data = json.load(file)
            return data[0]["forms"]


class ChatAPIServiceInterface:
    def execute_api_call(self, messages):
        raise NotImplementedError("This method should be overridden by subclasses")


class OpenAIChatAPIService(ChatAPIServiceInterface):
    def __init__(self, api_key, model_name="gpt-4o", temperature=1.0):
        self.api_service = ChatAPIService(api_key, model_name, temperature)

    def execute_api_call(self, messages):
        return self.api_service.execute_api_call(messages)


class FormParsingAgent:
    def __init__(self, chat_api_service):
        self.chat_api_service = chat_api_service

    def determine_relevant_form_selectors(self, forms, user_prompt):
        PROMPT_TEMPLATE = """
        You are an intelligent form parsing agent. Your task is to identify the most relevant forms based on the user's needs and provide the precise CSS selectors or XPaths for accessing these forms. 

        Forms Metadata: {forms}
        User Prompt: {user_prompt}

        Please evaluate the forms and return an array of objects, each containing:
        - "formPosition": the position of the form in the forms array.
        - "selectors": an array of strings where each string is either a CSS selector or an XPath that pinpoints a specific element within the form relevant to the user’s request.

        Your response should be in valid JSON format (no comments or extra whitespace) as follows:
        [
            {{
                "formPosition": <positionNumber>,
                "selectors": ["<selector1>", "<selector2>", ...],
                "reason": "<why this form is relevant>"
            }},
            ...
        ]
        """

        messages = [
            {
                "role": "system",
                "content": "You are a form parsing agent that determines if a form is relevant and provides selectors based on the user's prompt.",
            },
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(forms=forms, user_prompt=user_prompt),
            },
        ]

        response = self.chat_api_service.execute_api_call(messages)
        if response and "choices" in response:
            relevant_forms_info = response["choices"][0]["message"]["content"]
            relevant_forms_info = (
                relevant_forms_info.strip().removeprefix("```json").removesuffix("```")
            )
            return json.loads(relevant_forms_info)
        else:
            return "Error: Unable to determine relevant forms or selectors."


def main():
    # Load environment variables
    api_key = EnvironmentLoader.load_variable("OPENAI_API_KEY")

    # Load the forms data
    forms = FormLoader.load_forms("example2_westjet.json")

    # Initialize the FormParsingAgent with the OpenAIChatAPIService
    chat_api_service = OpenAIChatAPIService(api_key=api_key, temperature=0.2)
    agent = FormParsingAgent(chat_api_service)

    user_prompt = "I want to buy a plane ticket from Moncton to Montreal."

    relevant_forms_info = agent.determine_relevant_form_selectors(forms, user_prompt)

    print(
        "Relevant forms and their selectors:", json.dumps(relevant_forms_info, indent=4)
    )


if __name__ == "__main__":
    main()
