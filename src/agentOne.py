from http_api import ChatAPIService
import os
from dotenv import load_dotenv
import json

load_dotenv()


class FormParsingAgent:
    def __init__(self, api_key, model_name="gpt-4o", temperature=1.0):
        self.chat_api_service = ChatAPIService(api_key, model_name, temperature)

    def filter_relevant_forms(self, forms, user_prompt):
        PROMPT_TEMPLATE = """You are a form parsing agent that determines if a form is relevant based on the user's prompt.

                Forms: {forms}
                User prompt: {user_prompt}
                Look at the json metadata of each form and determine if a form will help the user accomplish his task.
                Answer the form position in the json array.
                answer in the following json format {{formArrayPosition:<positionNumber>, reason:<reason>}}"""

        messages = [
            {
                "role": "system",
                "content": "You are a form parsing agent that determines if a form is relevant based on the user's prompt.",
            },
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(forms=forms, user_prompt=user_prompt),
            },
        ]
        optional_parameters = {"response_format": {"type": "json_object"}}
        response = self.chat_api_service.execute_api_call(
            messages, **optional_parameters
        )
        if response and "choices" in response:
            relevant_form_indices = response["choices"][0]["message"]["content"]
            return relevant_form_indices
        else:
            return "Error: Unable to determine relevant forms."


def main():
    # Load the forms data from the westjet.json file
    with open("example2_westjet.json") as file:
        data = json.load(file)
        forms = data[0]["forms"]
    api_key = os.getenv("OPENAI_API_KEY")
    # Create an instance of the FormParsingAgent
    agent = FormParsingAgent(api_key=api_key)

    # User prompt
    user_prompt = "I want to buy a plane ticket from Moncton to Montreal."

    # Filter relevant forms based on the user prompt
    relevant_form_indices = agent.filter_relevant_forms(forms, user_prompt)

    print("Relevant form indices:", relevant_form_indices)


if __name__ == "__main__":
    main()
