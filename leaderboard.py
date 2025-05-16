

class Leaderboard:
    """ Functions for leaderboard calculations"""
    pass

class IQRanking:

    def __init__(self):
        # self.question_areas = self.calculate_areas()
        # self.question_weights = self.load_question_weights()
        pass


    @staticmethod
    def calculate_net_questions(self, area_answers):
        """ area_answers: [5,2,3] represents Correct,Incorrect,No Answer"""
        # For each area, the weights differ. So, this only returns one area net.
        net = area_answers[0] - area_answers[1]*0.25 - area_answers[2]*0.05
        return net

    def calculate_stem_iq(self, user_id):
        """ This should look at the total score on the stem_score in user
        progress (each question has a score for stem and verbal). And then the formula is
        stem_iq = score + [(160 - score) * percentage of correct questions in stem.]
        stem fields are math, ictm, biology, chemistry, physics. """

        # Get all user progress records for STEM fields
        stem_fields = ['math', 'ictm', 'biology', 'chemistry', 'physics']
        total_progress, stem_progress = self.query_db_for_user_progress(user_id, stem_fields)

        return self.calculate_iq_based_on_progress(total_progress, stem_progress, "stem")

    def calculate_verbal_iq(self, user_id):
        """ This should look at the total score on the verbal_score in user
        progress (each question has a score for stem and verbal). And then the formula is
        verbal_iq = score + [(160 - score) * percentage of correct questions in verbal.]
        verbal fields are language, geography, history, psychology. """

        # Get all user progress records for verbal fields
        verbal_fields = ['language', 'geography', 'history', 'psychology']
        total_progress, verbal_progress = self.query_db_for_user_progress(user_id, verbal_fields)

        return self.calculate_iq_based_on_progress(total_progress, verbal_progress, "verbal")

    @staticmethod
    def query_db_for_user_progress(user_id, fields):
        """ Query the database for user progress. """
        from models import UserProgress

        field_progress = UserProgress.query.filter(
            UserProgress.user_id == user_id,
            UserProgress.subject.in_(fields)
        ).all()

        total_progress = UserProgress.query.filter(
            UserProgress.user_id == user_id
        ).all()

        return total_progress, field_progress

    @staticmethod
    def calculate_iq_based_on_progress(total_progress, field_progress, field="stem"):
        """ Calculate IQ based on user progress. """

        if not total_progress or not field_progress:
            return 0

        # Calculate the total score and percentage of correct questions
        total_score = sum(p.stem_score if field=="stem" else p.verbal_score for p in total_progress)
        # correct_questions = sum(1 for p in field_progress if p.correct)
        # total_questions = len(field_progress)
        correct_questions = sum(1 for p in field_progress if p.correct)
        total_questions = sum(1 for p in field_progress if p.status != "skipped")

        # Calculate the percentage of correct questions
        percentage_correct = correct_questions / total_questions if total_questions > 0 else 0

        # Apply the formula: iq = score + [(160 - score) * percentage of correct questions]
        iq = total_score + ((160 - total_score) * percentage_correct)

        return max(0, round(iq, 2))
