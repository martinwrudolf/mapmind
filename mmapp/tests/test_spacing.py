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