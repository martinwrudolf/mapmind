from django.test import TestCase
from ..src.spacing import spacing_alg as sp
import numpy as np

class test_spacing(TestCase):
    def test_fdg(self):
        sim = np.random.rand(5,5)
        pos = sp.fruchterman_reingold(sim)

        for i in range(pos.shape[0]):
            for j in range(pos.shape[1]):
                self.assertIsNotNone(pos[i][j])


from django.test import TestCase
from numpy.testing import assert_array_equal
from ..src.spacing import spacing_alg as sp


class SimilarityScoresTestCase(TestCase):
    def test_num_scores_incremented(self):
        num_words = 5
        num_scores = 3
        words = ["apple", "banana", "orange", "peach", "pear"]

        scores = sp.similarity_scores(num_words, num_scores, words)

        self.assertEqual(scores.shape, (num_words, num_scores + 1))

    def test_scores_between_zero_and_one(self):
        num_words = 5
        num_scores = 3
        words = ["apple", "banana", "orange", "peach", "pear"]

        scores = sp.similarity_scores(num_words, num_scores, words)

        self.assertTrue((scores[:, 1:] >= 0).all())
        self.assertTrue((scores[:, 1:] <= 1).all())
