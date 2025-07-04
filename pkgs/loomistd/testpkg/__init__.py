import os
import random
import string

from loomi.service import SyncService
from loomi.spec import Spec


class TestSrv(SyncService):
    """
    Test service for Loomi.
    """

    def hello(self) -> str:
        """
        Simple method to return a greeting.
        """
        # Generate a random file name and path
        random_filename = (
            "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + ".txt"
        )
        # Generate a random sentence
        words = [
            "The",
            "quick",
            "brown",
            "fox",
            "jumps",
            "over",
            "lazy",
            "dog",
            "A",
            "smart",
            "cat",
            "sleeps",
            "on",
            "mat",
        ]
        random_sentence = " ".join(random.sample(words, random.randint(5, 10)))

        # Write the random sentence to the file
        with open(random_filename, "w") as f:
            f.write(random_sentence)

        return "Hello from TestSrv!"
