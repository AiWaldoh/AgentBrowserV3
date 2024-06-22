from http_api_async import ChatAPIService
import os
import json
from dotenv import load_dotenv

load_dotenv()


class FormParsingAgent:
    def __init__(self, chat_api_service):
        self.chat_api_service: ChatAPIService = chat_api_service

    async def determine_relevant_form_fields(self, form_data, user_prompt):
        PROMPT_TEMPLATE = f"""
        Given the following form data and user prompt, determine which fields are relevant and provide the CSS selectors for accessing them. Only return 1 selector per field.
        Don't forget that checkboxes and radio buttons have different values that need to be considered.
        Form data: {form_data}
        User prompt: {user_prompt}

        Answer in valid JSON format ONLY (no comments or extra whitespace) as follows:
        [
            {{
                "field_selector": "<field selector>",
                "value": "<value>",
                "reason": "<reason>"
            }},
        ]

        If no form data corresponds to the user prompt, return an empty list.
            ...
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant who understands the structure of forms.",
            },
            {"role": "user", "content": PROMPT_TEMPLATE},
        ]

        try:
            response = await self.chat_api_service.execute_api_call(
                messages=messages, **{"temperature": 0.2}
            )
            print(f"Response from API: {response}")

            if response and "choices" in response and len(response["choices"]) > 0:
                try:
                    field_mappings = json.loads(
                        response["choices"][0]["message"]["content"]
                    )
                    return field_mappings
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from API response: {e}")
                    return []
            else:
                print("No choices returned from API.")
                return []
        except Exception as e:
            print(f"Error determining relevant form fields: {str(e)}")
            return []
