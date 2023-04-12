from unittest import TestCase
from unittest.mock import MagicMock, patch
from mmapp.src.aws.aws_connection import inspect_on_ec2

class TestInspectOnEC2(TestCase):
    def setUp(self):
        self.clicked_word = "word"
        self.searched_words = ["word1", "word2"]
        self.corpus_path = "path/to/corpus"
        self.kv_path = "path/to/kv"
        self.kv_vector_path = "path/to/kv/vector"

    @patch("mmapp.src.aws.aws_connection.boto3.client")
    @patch("mmapp.src.aws.aws_connection.datetime")
    @patch("mmapp.src.aws.aws_connection.s3_write")
    def test_inspect_on_ec2(self, s3_write_mock, datetime_mock, boto3_client_mock):
        # Mock datetime.now() to return a constant value
        datetime_mock.now.return_value = "2023-04-12-00:00:00"

        # Mock the start_instances, get_waiter, and send_command methods
        ec2_instance_mock = MagicMock()
        boto3_client_mock.side_effect = [ec2_instance_mock, ec2_instance_mock]
        ec2_instance_mock.start_instances.return_value = {}
        ec2_instance_mock.send_command.return_value = {'Command': {'CommandId': '1234'}}

        # Call the function
        result = inspect_on_ec2(self.clicked_word, self.searched_words, self.corpus_path, self.kv_path, self.kv_vector_path)

        # Assert that the mocks were called with the expected arguments
        s3_write_mock.assert_called_once_with("internal-files/search_queries/2023-04-12-00:00:00.txt", "word1 word2")
        ec2_instance_mock.start_instances.assert_called_once_with(InstanceIds=["i-063cef059dc0f3ca7"])
        ec2_instance_mock.get_waiter.assert_called_with("command_executed")
        ec2_instance_mock.send_command.assert_called_once()



from unittest import TestCase
from unittest.mock import patch, MagicMock
import tempfile
import os
from mmapp.src.aws.aws_connection import s3_write, search_on_ec2

class TestSearchOnEC2(TestCase):
    def setUp(self):
        self.query = ["word1", "word2"]
        self.kv_path = "path/to/kv"
        self.kv_vectors_path = "path/to/kv/vector"
        self.vocab_path = "path/to/vocab"
        self.spellcheck = True
        self.notesonly = False

    @patch("mmapp.src.aws.aws_connection.boto3.client")
    @patch("mmapp.src.aws.aws_connection.datetime")
    @patch("mmapp.src.aws.aws_connection.s3_write")
    def test_search_on_ec2(self, s3_write_mock, datetime_mock, boto3_client_mock):
        # Mock datetime.now() to return a constant value
        datetime_mock.now.return_value = "2023-04-12-00:00:00"

        # Mock the start_instances, get_waiter, and send_command methods
        ec2_instance_mock = MagicMock()
        boto3_client_mock.return_value = ec2_instance_mock
        ec2_instance_mock.start_instances.return_value = {}
        ec2_instance_mock.send_command.return_value = {'Command': {'CommandId': '1234'}}
        ec2_instance_mock.get_command_invocation.return_value = {'StandardOutputContent': 'result_file'}

        # Create temporary files for the test
        with tempfile.NamedTemporaryFile(delete=False) as query_file:
            query_path = query_file.name
            s3_write_mock.side_effect = [s3_write(query_path, "word1 word2")]

            # Call the function
            result = search_on_ec2(self.query, self.kv_path, self.kv_vectors_path, self.vocab_path, self.spellcheck, self.notesonly)

            # Assert that the mocks were called with the expected arguments
            s3_write_mock.assert_called_once_with("internal-files/search_queries/2023-04-12-00:00:00.txt", "word1 word2")
            ec2_instance_mock.start_instances.assert_called_once_with(InstanceIds=["i-063cef059dc0f3ca7"])
            ec2_instance_mock.get_waiter.assert_called_with("command_executed")
            ec2_instance_mock.send_command.assert_called_once()

            # Clean up the temporary file
            os.remove(query_path)

        # Assert that the function returns the expected result
        self.assertEqual(result, 'result_file')


from unittest import TestCase
from unittest.mock import patch, MagicMock
from mmapp.src.aws.aws_connection import train_on_ec2

class TestTrainOnEC2(TestCase):
    def setUp(self):
        self.vocab_path = "path/to/vocab"
        self.kv_path = "path/to/kv"
        self.kv_vectors_path = "path/to/kv/vector"

    @patch("mmapp.src.aws.aws_connection.boto3.client")
    def test_train_on_ec2(self, boto3_client_mock):
        # Mock the start_instances, get_waiter, and send_command methods
        ec2_instance_mock = MagicMock()
        boto3_client_mock.return_value = ec2_instance_mock
        ec2_instance_mock.start_instances.return_value = {}
        ec2_instance_mock.send_command.return_value = {'Command': {'CommandId': '1234'}}

        # Call the function
        train_on_ec2(self.vocab_path, self.kv_path, self.kv_vectors_path)

        # Assert that the mocks were called with the expected arguments
        ec2_instance_mock.start_instances.assert_called_once_with(InstanceIds=["i-063cef059dc0f3ca7"])
        ec2_instance_mock.get_waiter.assert_called_with("command_executed")
        ec2_instance_mock.send_command.assert_called_once()


from unittest import TestCase
from unittest.mock import patch, MagicMock
from mmapp.src.aws.aws_connection import notebook_update_files

class TestNotebookUpdateFiles(TestCase):
    def setUp(self):
        self.notebook = MagicMock()
        self.notebook.vocab = "path/to/notebook/vocab"
        self.notebook.corpus = "path/to/notebook/corpus"

        self.note1 = MagicMock()
        self.note1.vocab = "path/to/note1/vocab"
        self.note1.corpus = "path/to/note1/corpus"

        self.note2 = MagicMock()
        self.note2.vocab = "path/to/note2/vocab"
        self.note2.corpus = "path/to/note2/corpus"

        self.notes_list = [self.note1, self.note2]

    @patch("mmapp.src.aws.aws_connection.s3_read")
    @patch("mmapp.src.aws.aws_connection.s3_write")
    def test_notebook_update_files(self, s3_write_mock, s3_read_mock):
        # Set up s3_read mock return values
        s3_read_mock.side_effect = [
            "note1_vocab", "note1_corpus",
            "note2_vocab", "note2_corpus"
        ]

        # Call the function
        notebook_update_files(self.notebook, self.notes_list)

        # Assert that the mocks were called with the expected arguments
        s3_read_mock.assert_any_call(self.note1.vocab)
        s3_read_mock.assert_any_call(self.note1.corpus)
        s3_read_mock.assert_any_call(self.note2.vocab)
        s3_read_mock.assert_any_call(self.note2.corpus)

        s3_write_mock.assert_any_call(self.notebook.vocab, "note1_vocab note2_vocab")
        s3_write_mock.assert_any_call(self.notebook.corpus, "note1_corpus note2_corpus")
