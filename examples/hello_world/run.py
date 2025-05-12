import asyncio

from loomi import AsyncApp, Context, Operation, Spec
from loomistd.aexecutor import ExecutionEngineSpec
from loomistd.state import StateSpec


class HelloWorldApp(AsyncApp):
    """A simple hello world app with multiple languages."""

    async def initialize_greetings(self, context: Context):
        """Store greetings in different languages in state."""
        greetings = {
            "english": "Hello, World!",
            "spanish": "¡Hola, Mundo!",
            "french": "Bonjour, Monde!",
            "german": "Hallo, Welt!",
            "italian": "Ciao, Mondo!",
            "portuguese": "Olá, Mundo!",
            "dutch": "Hallo, Wereld!",
            "russian": "Привет, мир!",
            "japanese": "こんにちは世界!",
            "chinese": "你好，世界！",
            "korean": "안녕하세요, 세계!",
            "arabic": "مرحبا بالعالم!",
            "hindi": "नमस्ते, दुनिया!",
            "armenian": "Բարև՜, աշխարհ։",
        }

        # Store the greetings in state
        context.scope.dict("greetings").store(greetings)

    async def say_greeting(self, context: Context):
        """Say a single greeting."""
        # Map operation provides the current key in the context
        language = context["map_key"]
        greeting = context.scope.dict("greetings").get(language)
        print(f"{language.capitalize()}: {greeting}")

    def define(self) -> Operation:
        """Define the workflow for this app."""
        return self.ex.Sequence(
            # 1. Initialize the greetings in state
            self.ex.Function(self.initialize_greetings),
            # 2. Process each greeting using Map with a delay
            self.ex.Map(
                self.ex.Sequence(
                    self.ex.Function(self.say_greeting),
                    self.ex.Delay(0.75),  # Add delay between greetings
                ),
                items_path=("_", "greetings"),
                max_concurrency=2,  # Process 2 greetings concurrently
            ),
        )


async def main():
    # Create and run the application
    async with HelloWorldApp(
        Spec(factory=HelloWorldApp),
        state_spec=StateSpec(),
        executor_spec=ExecutionEngineSpec(),
    ) as app:
        await app.start()


if __name__ == "__main__":
    asyncio.run(main())
