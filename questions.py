import random

from dotenv import load_dotenv
# from pprint import pprint
# import requests
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
        self.stem_weight = 1
        self.verbal_weight = 1
        # Each question should have weight based on the area.
        #  For example, physics and math questions should give 4 sayisal points but 1 sozel point
        #  whereas a geography question should be 2 sayısal, 3 sözel points.

        # A question is multiple choice if answer is ABCDE,
        #  If not, it is an exact answer.
        #  Have a template to choose if MC. If not, have a text bar.

    def __str__(self):
        return f"{self.subject}_{self.name}"

    def print_question(self):
        print(f"{self.subject}_{self.name}")

    def display_image(self):
        return self.question_path

    def assign_weight(self, stem_weight, verbal_weight):
        self.stem_weight = stem_weight
        self.verbal_weight = verbal_weight

class Weights:
    """ Define the weights of the areas. """

    def __init__(self):
        self.weights = self.load_question_weights()

    @staticmethod
    def load_question_weights():
        """ Weights of each subject. Tuple of Sayisal and Sozel constants."""
        # Maybe this should take the values from a csv?
        weights = {
            "ictm": (5, 1),
            "math": (4, 1),
            "physics": (4, 1),
            "biology": (4, 2),
            "chemistry": (4, 1),
            "world_history": (1, 4),
            "history": (1, 4),
            "turkish_history": (1, 4),
            "us_history": (1, 4),
            "geography": (2, 4),
            "language": (1, 4),
            "psychology": (2, 4),
        }

        return weights

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
        - Give a Turkish map, and ask which city
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

        the final data that will be loaded is as follows.

        questions = {
            "physics":[pq1_obj, pq2_obj, pq3_obj],
            "ictm":[iq1_obj, iq2_obj, iq3_obj, iq4_obj],
            "psychology":[sq1_obj, sq2_obj],
        }
        """
        image_files = Path(path).glob('*/*')
        # image_files = glob.glob(path)
        w = Weights()

        questions = {}

        # This should also extract the interest area based on the names
        #  To do this, I can carry each interest area to its folder, then
        #  use the folder name as the key.
        # This should return a dictionary instead
        for image_path in image_files:
            image_name, question_answer = str(image_path.with_suffix('').name).split("_")
            if ".DS" in image_name:
                # Mac constantly creates this file even though unnecessary.
                continue

            image_folder = image_path.parent.name
            # Store relative path instead of full path for proper static file serving
            relative_path = f"{image_folder}/{image_path.name}"
            question = Question(name=image_name, subject=image_folder,
                                question_path=relative_path,
                                answer=question_answer,
                                )

            # Assign STEM vs Art weights.
            question.assign_weight(*w.weights[image_folder])

            print(#f"{question=} "
                  f"{question.name=} "
                  f"{question.subject=} "
                  f"{question.question_path=} "
                  f"{question.stem_weight=} "
                  f"{question.verbal_weight=} ")

            if image_folder in questions:
                questions[image_folder].append(question)
            else:
                questions[image_folder] = [question]


        # Assuming the images are needed as the file path.
        return questions

    @staticmethod
    def extract_question_from_path(image_path):
        """ Read the image and return a shape."""
        # I don't exactly know if this is necessary, but I assume so.
        #  Most likely image_path can be directly called from frontend.

        image = image_path # do action to image_path
        return image

    def select_question_random(self) -> Question:
        """ Select a random question from a random interest area. """
        rand_subject = random.choice(list(self.questions.keys()))
        rand_index = random.randint(0, len(self.questions[rand_subject]) - 1)
        rand_question = self.questions[rand_subject][rand_index]
        return rand_question

    def select_unanswered_question(self, user_id) -> Question:
        """ Select a random question that the user has not answered yet.

        Args:
            user_id: The ID of the current user

        Returns:
            A random question that the user has not answered yet, or None if all questions have been answered
        """
        from models import UserProgress

        # Get all questions the user has answered (not skipped)
        answered_questions = UserProgress.query.filter_by(
            user_id=user_id, 
            status='answered'
        ).all()

        # Create a set of (subject, name) tuples for quick lookup
        answered_set = {(q.subject, q.question_name) for q in answered_questions}

        # Create a list of all available questions that haven't been answered
        available_questions = []

        for subject, question_list in self.questions.items():
            for question in question_list:
                if (subject, question.name) not in answered_set:
                    available_questions.append(question)

        # If there are no unanswered questions, return None
        if not available_questions:
            return None

        # Select a random question from the available ones
        return random.choice(available_questions)

    def select_question_by_interest(self, interest_area: str):
        """ Select the question based on users selection on interests."""
        int_questions = self.get_questions_of_interest(interest_area)
        int_question = int_questions[random.randint(0, len(int_questions)-1)]
        return int_question

    def get_questions_of_interest(self, interest_area):
        return self.questions[interest_area]


if __name__ == "__main__":
    print("Questions invoked from CLI.")
    questions = Questions()
    area = input("Enter interest area: ")
    area_question = questions.select_question_by_interest(area)
    print(area_question.print_question())
    print(questions.select_question_random())
