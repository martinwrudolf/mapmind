from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
import docx
from ..src.ML import machine_learning as ml
import os
import pickle
import numpy as np
from gensim.models import KeyedVectors
import sys

class test_ML(TestCase):
    def test_process_user_notes(self):
        document = docx.Document()
        document.add_paragraph("hello world! I am testing - punctuation. test-word")
        document.save('test.docx')

        file = open('test.docx', 'rb')
        test_contents = bytes("hello world! testing - punctuation. test-word", 'utf-8')
        test_file = SimpleUploadedFile("test.docx", file.read(), content_type='application/msword')
        file.close()
        keys = ["hello", "testing", "punctuation"]
        oov, vocab, corpus = ml.process_user_notes(test_file, keys)

        #oov
        self.assertSetEqual(set(oov), {"world", "test-word"})
        self.assertIn("world", oov)
        self.assertIn("test-word", oov)
        self.assertEqual(len(oov), 2)

        #vocab
        self.assertEqual(vocab, "hello world testing punctuation test-word")

        # corpus
        self.assertEqual(corpus, "hello world i am testing  punctuation test-word")
        
        os.remove('test.docx')

    def test_remove_stop_words(self):
        corpus = "this is my corpus. John Cleese. I am blue! My favourite is red"
        vocab = ml.remove_stop_words(corpus)
        self.assertEqual(vocab, "corpus. john cleese. blue! favourite red")

    def test_load_embeddings_from_txt(self):
        txt = b'the 0.04656 0.21318\nhello 0.40 0.50\njohn 0.20 -0.456\ntest 0.79 0.29\n'
        path2txt = "test.txt"
        with open(path2txt, 'wb') as f:
            f.write(txt)
        embed = ml.load_embeddings_from_txt(path2txt)
        
        test_dict = {
            'the': [0.04656, 0.21318],
            'hello': [0.40, 0.50],
            'john': [0.20, -0.456],
            'test': [0.79, 0.29]
        }
        self.assertDictEqual(embed, test_dict)
        os.remove('test.txt')

    def test_save_embeddings(self):
        embed = {
            'the': [0.04656, 0.21318],
            'hello': [0.40, 0.50],
            'john': [0.20, -0.456],
            'test': [0.79, 0.29]
        }
        path2pkl = "test.pkl"
        ml.save_embeddings(embed, path2pkl)

        self.assertTrue(os.path.exists("test.pkl"))

        with open(path2pkl, 'rb') as f:
            test_embed = pickle.load(f)
        
        self.assertDictEqual(embed, test_embed)
        os.remove('test.pkl')

    def test_load_embeddings(self):
        embed = {
            'the': [0.04656, 0.21318],
            'hello': [0.40, 0.50],
            'john': [0.20, -0.456],
            'test': [0.79, 0.29]
        }
        path2pkl = "test.pkl"

        with open(path2pkl, 'wb') as f:
            pickle.dump(embed, f)
        
        test_embed = ml.load_embeddings(path2pkl)
        self.assertDictEqual(embed, test_embed)
        os.remove('test.pkl')

    def test_create_cooccurrence(self):
        vocab = "name name name claire hello"
        oov = ["claire", "hello"]

        arr = ml.create_cooccurrence(vocab,oov)
        self.assertTrue(np.array_equal(arr, np.array([[0, 1], [1, 0]])))

    def test_train_mittens(self):
        arr = np.array([[0,1],[1,0]])
        oov = ["claire", "hello"]
        embed = {
            "name": np.random.rand(300)
        }
        new_embed = ml.train_mittens(arr, oov, embed)

        self.assertEqual(len(new_embed), 3)
        self.assertIsNotNone(new_embed["claire"])
        self.assertIsNotNone(new_embed["hello"])
        self.assertEqual(len(new_embed["claire"]), 300)
        self.assertEqual(len(new_embed["hello"]), 300)

    def test_create_kv_from_embed(self):
        embed = {
            "name": np.random.rand(300),
            "claire": np.random.rand(300),
            "hello": np.random.rand(300)
        }
        kv = ml.create_kv_from_embed(embed)

        self.assertIsInstance(kv, KeyedVectors)
        self.assertEqual(len(kv), 3)

        self.assertIsNotNone(kv["name"])
        self.assertIsNotNone(kv["claire"])
        self.assertIsNotNone(kv["hello"])

        self.assertIsNotNone(kv.most_similar("name"))
        self.assertIsNotNone(kv.most_similar("claire"))
        self.assertIsNotNone(kv.most_similar("hello"))

        self.assertIsNotNone(kv.similarity("claire", "hello"))
        self.assertIsNotNone(kv.similarity("name", "hello"))
        self.assertIsNotNone(kv.similarity("claire", "name"))
    
    def test_model_quality(self):
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.split(current_directory)[0]
        file_path = os.path.join(parent_directory, 'ml_models', 'glove.pkl')
        embed = ml.load_embeddings(file_path)
        kv = ml.create_kv_from_embed(embed)
        # test bidirectional similarity
        self.assertEqual(kv.similarity("red", "hello"), kv.similarity("hello", "red"))
        self.assertEqual(kv.similarity("hello", "name"), kv.similarity("name", "hello"))
        self.assertEqual(kv.similarity("name", "red"), kv.similarity("red", "name"))

        # test triangle inequality
        self.assertLess(kv.distance("red", "hello"), kv.distance("red", "name") + kv.distance("name", "hello"))
        self.assertLess(kv.distance("hello", "name"), kv.distance("red", "name") + kv.distance("red", "hello"))
        self.assertLess(kv.distance("red", "name"), kv.distance("red", "hello") + kv.distance("name", "hello"))
    
    def test_save_and_load_kv(self):
        embed = {
            "name": np.random.rand(300),
            "claire": np.random.rand(300),
            "hello": np.random.rand(300)
        }
        kv = KeyedVectors(300)
        kv.add_vectors(list(embed.keys()), list(embed.values()))

        ml.save_kv(kv, "test_kv")
        self.assertTrue(os.path.exists("test_kv"))

        loaded_kv = ml.load_kv("test_kv")
        self.assertIsInstance(loaded_kv, KeyedVectors)
        self.assertEqual(len(kv), 3)

        self.assertIsNotNone(kv["name"])
        self.assertIsNotNone(kv["claire"])
        self.assertIsNotNone(kv["hello"])
        self.assertIsNotNone(kv.most_similar("name"))
        self.assertIsNotNone(kv.most_similar("claire"))
        self.assertIsNotNone(kv.most_similar("hello"))
        self.assertIsNotNone(kv.similarity("claire", "hello"))
        self.assertIsNotNone(kv.similarity("name", "hello"))
        self.assertIsNotNone(kv.similarity("claire", "name"))

        os.remove('test_kv')

    def test_search(self):
        words = ["hello", "red", "car", "computer"]
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.split(current_directory)[0]
        file_path = os.path.join(parent_directory, 'ml_models', 'glove.pkl')
        embed = ml.load_embeddings(file_path)
        kv = ml.create_kv_from_embed(embed)

        vocab = "here is a fake vocabulary thing"

        mat, result_words, skipwords = ml.search(words, kv, 2, vocab)

        # entire thing should exist
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                self.assertIsNotNone(mat[i][j])

        # want as many or more result words than words
        self.assertGreaterEqual(len(result_words), len(words))

        for w in words:
            self.assertIn(w, result_words)
        
        self.assertEqual(len(skipwords), 0)

        mat, result_words, skipwords = ml.search(["asdkfelsfl"], kv, 2, vocab)
        print(result_words)
        self.assertIn("asdkfelsfl", skipwords)
        self.assertEqual(len(result_words), 0)
        
    def test_inspect_node(self):
        words = ["hello", "red", "car", "computer"]
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.split(current_directory)[0]
        file_path = os.path.join(parent_directory, 'ml_models', 'glove.pkl')
        embed = ml.load_embeddings(file_path)
        kv = ml.create_kv_from_embed(embed)

        word = "hello"
        searched = ["hello", "world"]
        corpus = "hi hey hello world this is my corpus it is very long I am not sure what else to write but here we are"

        results = ml.inspect_node(word, searched, corpus, kv)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "hi hey hello world this is my corpus it is very long")
