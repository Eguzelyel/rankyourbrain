

class Leaderboard:
    """ Functions for leaderboard calculations"""
    pass

class QuestionRanking:

    def __init__(self):
        # self.question_areas = self.calculate_areas()
        self.question_weights = self.load_question_weights()

    @staticmethod
    def load_question_weights(self):
        """ Weights of each subject. Tuple of Sayisal and Sozel constants."""
        # Maybe this should take the values from a csv?
        weights = {
            "ictm": (5,1),
            "math": (4,1),
            "physics": (4,1),
            "biology": (4,2),
            "chemistry": (4,1),
            "world_history": (1,4),
            "turkish_history": (1,4),
            "us_history": (1,4),
        }

        # for area in self.question_areas:
        #     if area not in weights:
        #         weights[area] = (2,2)
        return weights

    @staticmethod
    def calculate_net_questions(self, area_answers):
        """ area_answers: [5,2,3] represents Correct,Incorrect,No Answer"""
        # For each area, the weights differ. So, this only returns one area net.
        net = area_answers[0] - area_answers[1]*0.25 - area_answers[2]*0.05
        return net

