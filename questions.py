import random

from dotenv import load_dotenv
from pprint import pprint
import requests
import logging
import settings
from pathlib import Path


logger = logging.getLogger()
load_dotenv()


# Turn this into a class structure.
#  And then, also try to add tests.
def get_question():
    """ Get a new question main function."""

    pass


class Question:

    def __init__(self, name, subject, question_path, answer):
        self.name = name
        self.subject = subject
        self.question_path = question_path
        self.answer = answer
        # Each question should have weight based on the area.
        #  for example physics and math questions should give 4 sayisal point but 1 sozel point
        #  whereas a geography question should be 2 sayisal, 3 sozel point.

        # A question is multiple choice if answer is ABCDE,
        #  If not, it is an exact answer.
        #  Have a template to choose if MC. If not, have a text bar.

    def __str__(self):
        return f"{self.subject}_{self.name}"

    def print_question(self):
        print(f"{self.subject}_{self.name}")

    def display_image(self):
        return self.question_path

class Questions:
    """ Question type ideas.
     Chess question, find which piece should move.
     IQ test question, find the next in the pattern.
     Physics AP question, actual question.
     Mathematics high school level questions.
        - Typical geometry questions
     Mathematics olympiad level questions.
        - Number theory, such as x2+y2=x+y type
        - ICTM practice questions.
     Biology question, mostly reasoning.
     Chemistry question, easier topics.
     Language
        - Find the similar words
        - Turkce yazim kilavuzu
     Geography
        - Give a map and ask which country
        - Give Turkish map, and ask which city
     Psychology, reasoning question.

    """

    def __init__(self, questions_path=settings.questions_path):
        self.questions = self.load_questions(questions_path)


    @staticmethod
    def load_questions(path: str) -> dict:
        """
        Args:
            path: String questions directory

        Returns:
            questions: dict of list of Question objects

        Final data that will be loaded is as follows.

        questions = {
            "physics":[pq1_obj, pq2_obj, pq3_obj],
            "ictm":[iq1_obj, iq2_obj, iq3_obj, iq4_obj],
            "psychology":[sq1_obj, sq2_obj],
        }
        """
        image_files = Path(path).glob('*/*')
        # image_files = glob.glob(path)

        questions = {}

        # This should also extract the interest area based on the names
        #  To do this, I can carry each interest area to its folder, then
        #  use folder name as the key.
        # This should return a dictionary instead
        for image_path in image_files:
            image_name, question_answer = str(image_path.with_suffix('').name).split("_")
            if image_name == ".DS_Store":
                # Mac constantly creates this file even though unnecessary.
                continue

            image_folder = image_path.parent.name
            question = Question(name=image_name, subject=image_folder,
                                question_path=str(image_path),
                                answer=question_answer,
                                )
            print(f"{question=} "
                  f"{question.name=} "
                  f"{question.subject=} "
                  f"{question.question_path=} ")

            if image_folder in questions:
                questions[image_folder].append(question)
            else:
                questions[image_folder] = [question]


        # Assuming the images are needed as file path.
        return questions

    @staticmethod
    def extract_question_from_path(image_path):
        """ Read the image, and return a shape."""
        # I don't exactly know if this is necessary, but I assume so.
        #  Most likely image_path can be directly called from frontend.

        image = image_path # do action to image_path
        return image

    def select_question_random(self) -> Question:
        """ Select a random question from random interest area. """
        rand_subject = self.questions[random.randint(0, len(self.questions))]
        rand_question = self.questions[rand_subject].pop(
            random.randint(
            0, len(self.questions[rand_subject]))
        )
        return rand_question

    def select_question_by_interest(self, interest_area: str):
        """ Select the question based on users selection on interests."""
        int_questions = self.get_questions_of_interest(interest_area)
        int_question = int_questions[random.randint(0, len(int_questions))]
        return int_question

    def get_questions_of_interest(self, interest_area):
        return self.questions[interest_area]

