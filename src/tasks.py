from abc import ABC, abstractmethod
import json


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
        print(task)
        if task:
            return task.execute(json.loads(arguments), dependencies_container)
        else:
            print(f"Task '{task_name}' not found.")
            return None


class Task(ABC):
    @abstractmethod
    def execute(self, arguments):
        pass


class GoToPageTask(Task):
    async def execute(self, arguments, dependencies_container):
        browser = dependencies_container.get("web_browser")
        if browser:
            print(f"Go to page {arguments['url']}")
            await browser.navigate_to(arguments["url"])
            await browser.wait_for_navigation()

        pass
