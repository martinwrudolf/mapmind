import json
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from mmapp.models import Notebook, Note
from mmapp.views import inspect_node, login
from django.http import QueryDict

class LoginViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        self.another_user = User.objects.create_user(
            username="anotheruser3",
            email="anotheremail3@email.com",
            password="anotherpassword3"
        )
        self.notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )
        self.note = Note.objects.create(
            file_name='testnote3',
            file_type='text/plain',
            owner=self.user,
            notebooks=self.notebook,
            vocab='vocab',
            corpus='corpus'
        )

    def test_login_authenticated(self):
        request = self.factory.get('/login/')
        request.user = self.user
        response = login(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_login_not_authenticated(self):
        request = self.factory.get('/login/')
        request.user = AnonymousUser()
        response = login(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/')


from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from mmapp.models import Notebook, Note
from mmapp.views import register

class RegisterViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        
    def test_register_authenticated(self):
        request = self.factory.get('/register/')
        request.user = self.user
        response = register(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_register_get_request(self):
        request = self.factory.get('/register/')
        request.user = AnonymousUser()
        response = register(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/register/')

    def test_register_non_unique_username(self):
        request = self.factory.post('/register/', {
            'username': 'testuser3',
            'email': 'newemail@email.com',
            'password': 'newpassword',
        })
        request.user = AnonymousUser()
        response = register(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Username is not unique!")

    def test_register_non_unique_email(self):
        request = self.factory.post('/register/', {
            'username': 'newusername',
            'email': 'testemail3@email.com',
            'password': 'newpassword',
        })
        request.user = AnonymousUser()
        response = register(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Email is not unique!")

    def test_register_invalid_password(self):
        request = self.factory.post('/register/', {
            'username': 'newusername',
            'email': 'newemail@email.com',
            'password': 'short',  # Invalid password
        })
        request.user = AnonymousUser()
        response = register(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Password is not valid!")

    def test_register_valid_registration(self):
        request = self.factory.post('/register/', {
            'username': 'newusername',
            'email': 'newemail@email.com',
            'password': 'newvalidpassword',
        })
        request.user = AnonymousUser()
        response = register(request)
        self.assertEqual(response.status_code, 201)


import os
import tempfile
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User, AnonymousUser
from mmapp.models import Notebook, Note
from mmapp.views import upload
from unittest.mock import MagicMock, patch

class UploadViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        self.notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )

    def test_upload_not_authenticated(self):
        request = self.factory.post('/upload/')
        request.user = AnonymousUser()
        response = upload(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/')

    def test_upload_get_request(self):
        request = self.factory.get('/upload/')
        request.user = self.user
        response = upload(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/notebooks')

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_invalid_file_format(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as img_file:
            img_file.write(b"Dummy file content")
            img_file.seek(0)
            request = self.factory.post('/upload/', {
                'file': img_file,
                'notebook': self.notebook.id,
            })
            request.user = self.user
            response = upload(request)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "File is not of correct format")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_large_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as txt_file:
            txt_file.write(b"Dummy file content" * 200000)  # Create a file larger than 450KB
            txt_file.seek(0)
            request = self.factory.post('/upload/', {
                'file': txt_file,
                'notebook': self.notebook.id,
            })
            request.user = self.user
            response = upload(request)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "File is too large")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('mmapp.views.aws.s3_read')
    def test_upload_existing_file(self, mock_s3_read):
        # Create a Note with a specific file name
        note = Note.objects.create(
            file_name='existing_file.txt',
            file_type='text/plain',
            owner=self.user,
            notebooks=self.notebook,
            vocab='vocab',
            corpus='corpus'
        )

        mock_s3_read.side_effect = ["dummy_vocab", "dummy_corpus"]
        with tempfile.NamedTemporaryFile(suffix=".txt") as txt_file:
            txt_file.write(b"Dummy file content")
            txt_file.seek(0)
            request = self.factory.post('/upload/', {
                'file': txt_file,
                'notebook': self.notebook.id,
            })
            request.user = self.user
            response = upload(request)
            response = upload(request)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "Note file already exists in this notebook")

    
    def test_upload_notebook_does_not_exist(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as txt_file:
            txt_file.write(b"Dummy file content")
            txt_file.seek(0)
            request = self.factory.post('/upload/', {
                'file': txt_file,
                'notebook': 999,
            })
            request.user = self.user
            response = upload(request)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "Notebook does not exist")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('mmapp.views.aws.s3_write')
    @patch('mmapp.views.aws.s3_read')
    @patch('mmapp.views.aws.train_on_ec2')
    @patch('mmapp.views.ml.load_embeddings')
    @patch('mmapp.views.ml.process_user_notes')
    def test_upload_valid_file(self, mock_process_user_notes, mock_load_embeddings, mock_train_on_ec2, mock_s3_read, mock_s3_write):
        mock_load_embeddings.return_value = ["embedding1", "embedding2"]
        mock_process_user_notes.return_value = ([], "dummy_vocab", "dummy_corpus", [])
        mock_s3_read.side_effect = ["dummy_vocab", "dummy_corpus"]
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as txt_file:
            txt_file.write(b"Dummy file content")
            txt_file.seek(0)
            request = self.factory.post('/upload/', {
                'file': txt_file,
                'notebook': self.notebook.id,
            })
            request.user = self.user
            response = upload(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), "File uploaded successfully")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch('mmapp.views.aws.s3_write')
    @patch('mmapp.views.aws.s3_read')
    @patch('mmapp.views.aws.train_on_ec2')
    @patch('mmapp.views.ml.load_embeddings')
    @patch('mmapp.views.ml.process_user_notes')
    def test_upload_missing_vocab_or_corpus(self, mock_process_user_notes, mock_load_embeddings, mock_train_on_ec2, mock_s3_read, mock_s3_write):
        mock_load_embeddings.return_value = ["embedding1", "embedding2"]
        mock_process_user_notes.return_value = ([], "dummy_vocab", "dummy_corpus", [])
        mock_s3_read.side_effect = [Exception("Missing vocab"), "dummy_vocab", Exception("Missing corpus"), "dummy_corpus"]

        with tempfile.NamedTemporaryFile(suffix=".txt") as txt_file:
            txt_file.write(b"Dummy file content")
            txt_file.seek(0)

            # Test when notebook doesn't have an associated vocab
            request = self.factory.post('/upload/', {
                'file': txt_file,
                'notebook': self.notebook.id,
            })
            request.user = self.user
            response = upload(request)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "Database error: Notebook does not have a vocab file")

            # Test when notebook doesn't have an associated corpus
            request = self.factory.post('/upload/', {
                'file': txt_file,
                'notebook': self.notebook.id,
            })
            request.user = self.user
            response = upload(request)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "Database error: Notebook does not have a corpus file")


from django.http import HttpResponse, HttpRequest, JsonResponse
from unittest.mock import MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from mmapp.views import create_notebook, delete_notebook, edit_notebook, merge_notebooks, notebooks

class NotebookViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        self.notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )

    def test_create_notebook(self):
        request = HttpRequest()

        # Test user authentication check
        request.user = AnonymousUser()
        request.method = 'POST'
        response = create_notebook(request)
        self.assertEqual(response.status_code, 401)

        # Test successful notebook creation
        request.user = self.user
        request.method = 'POST'
        request.POST = {'notebook': 'New Notebook'}

        with patch('mmapp.views.aws.s3_write') as mock_s3_write:
            response = create_notebook(request)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.content.decode(), "Notebook created successfully")
            mock_s3_write.assert_called()

        # Test notebook already exists
        Notebook.objects.create(
            name='Existing Notebook',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )
        request.POST = {'notebook': 'Existing Notebook'}
        response = create_notebook(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Notebook already exists")

        # Test invalid HTTP method
        request.method = 'GET'
        response = create_notebook(request)
        self.assertEqual(response.status_code, 405)


    def test_delete_notebook(self):
        request = HttpRequest()

        # Test user authentication check
        request.user = AnonymousUser()
        request.method = 'POST'
        response = delete_notebook(request)
        self.assertEqual(response.status_code, 401)

        # Test successful notebook deletion
        request.user = self.user
        request.method = 'POST'

        notebook = Notebook.objects.create(
            name='Notebook to Delete',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )

        request.POST = {'notebook': notebook.id}

        with patch('mmapp.views.aws.s3_delete_folder') as mock_s3_delete_folder:
            response = delete_notebook(request)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.content.decode(), "Notebook deleted successfully")
            mock_s3_delete_folder.assert_called()

        # Test invalid HTTP method
        request.method = 'GET'
        response = delete_notebook(request)
        self.assertEqual(response.status_code, 405)

    def test_edit_notebook(self):
        request = HttpRequest()

        # Test user authentication check
        request.user = AnonymousUser()
        response = edit_notebook(request)
        self.assertEqual(response.status_code, 302)

        # Test edit_notebook endpoint
        request.user = self.user
        response = edit_notebook(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "This is the URL where we edit notebooks!")

    def test_merge_notebooks(self):
        request = HttpRequest()

        # Test user authentication check
        request.user = AnonymousUser()
        request.method = 'POST'
        response = merge_notebooks(request)
        self.assertEqual(response.status_code, 401)

        # Test merge_notebooks successful case
        request.user = self.user
        request.method = 'POST'

        notebook1 = Notebook.objects.create(
            name='Notebook1',
            owner=self.user,
            vocab='vocab1',
            corpus='corpus1',
            kv='kv1',
            kv_vectors='kv_v1'
        )

        notebook2 = Notebook.objects.create(
            name='Notebook2',
            owner=self.user,
            vocab='vocab2',
            corpus='corpus2',
            kv='kv2',
            kv_vectors='kv_v2'
        )

        self.note = Note.objects.create(
            file_name='testnote3',
            file_type='text/plain',
            owner=self.user,
            notebooks=notebook1,
            vocab='vocab',
            corpus='corpus'
        )


        request.POST = QueryDict('', mutable=True)
        request.POST.setlist('notebooks[]', [notebook1.id, notebook2.id])
        request.POST['merged_notebook_name'] = 'MergedNotebook'

        with patch('mmapp.views.aws.move_file') as mock_move_file, \
             patch('mmapp.views.aws.s3_delete_folder') as mock_s3_delete_folder, \
             patch('mmapp.views.aws.notebook_update_files') as mock_notebook_update_files, \
             patch('mmapp.views.aws.train_on_ec2') as mock_train_on_ec2, \
                patch('mmapp.views.aws.s3_read') as mock_s3_read:
            
            mock_s3_read.return_value = 'sample_vocab_value'

            response = merge_notebooks(request)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.content.decode(), "Notebooks merged successfully")
            mock_move_file.assert_called()
            mock_s3_delete_folder.assert_called()
            mock_notebook_update_files.assert_called()
            mock_train_on_ec2.assert_called()

        # Test invalid HTTP method
        request.method = 'GET'
        response = merge_notebooks(request)
        self.assertEqual(response.status_code, 405)


    def test_notebooks(self):
        request = HttpRequest()

        # Test user authentication check
        request.user = AnonymousUser()
        response = notebooks(request)
        self.assertEqual(response.status_code, 302)

        # Test notebooks view rendering
        request.user = self.user
        response = notebooks(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'notebooks')



from mmapp.views import delete_notes

class NoteViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        self.notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )


    def test_delete_notes(self):
        request = HttpRequest()

        # Test user authentication check
        request.user = AnonymousUser()
        request.method = 'POST'
        response = delete_notes(request)
        self.assertEqual(response.status_code, 401)

        # Test successful notes deletion
        request.user = self.user
        request.method = 'POST'

        notebook = Notebook.objects.create(
            name='Notebook for Note Deletion',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )

        note = Note.objects.create(
            file_name='Note to Delete',
            file_type='text/plain',
            owner=self.user,
            notebooks=notebook,
            vocab='vocab',
            corpus='corpus'
        )

        request.POST = QueryDict('', mutable=True)
        request.POST.setlist('note', [note.id])

        with patch('mmapp.views.aws.s3_delete_folder') as mock_s3_delete_folder, \
            patch('mmapp.views.aws.notebook_update_files') as mock_notebook_update_files, \
            patch('mmapp.views.aws.train_on_ec2') as mock_train_on_ec2, \
                patch('mmapp.views.aws.s3_read') as mock_s3_read:
            
            mock_s3_read.return_value = 'sample_vocab_value'

            response = delete_notes(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), "Notes deleted successfully")
            mock_s3_delete_folder.assert_called()
            mock_notebook_update_files.assert_called()
            mock_train_on_ec2.assert_called()

        # Test invalid HTTP method
        request.method = 'GET'
        response = delete_notes(request)
        self.assertEqual(response.status_code, 405)



from mmapp.views import edit_username, edit_email, delete_account, settings
class AccountViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        self.notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )

    def test_settings(self):
        request = HttpRequest()

        # Test user authentication check
        request.method = 'GET'
        request.user = AnonymousUser()
        response = settings(request)
        assert response.status_code == 302
        assert response.url == '/accounts/login/'

        # Test settings view
        request.user = self.user
        response = settings(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'settings')


    def test_edit_username(self):
        request = HttpRequest()

        # Test user authentication check
        request.method = 'POST'
        request.user = AnonymousUser()
        response = edit_username(request)
        self.assertEqual(response.status_code, 401)

        # Test edit_username with non-unique username
        request.user = self.user
        request.POST = {"username": "existing_user"}
        response = edit_username(request)
        response = edit_username(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Username is not unique!")

        # Test edit_username successful case
        request.POST = {"username": "new_unique_username"}
        response = edit_username(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content.decode(), "Username edited successfully!")

        # Test invalid HTTP method
        request.method = 'GET'
        response = edit_username(request)
        self.assertEqual(response.status_code, 405)

    def test_edit_email(self):
        request = HttpRequest()

        # Test user authentication check
        request.method = 'POST'
        request.user = AnonymousUser()
        response = edit_email(request)
        self.assertEqual(response.status_code, 401)

        # Test edit_email with non-unique email
        request.user = self.user
        request.POST = {"email": "existing_user@example.com"}
        response = edit_email(request)
        response = edit_email(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Email is not unique!")

        # Test edit_email successful case
        request.POST = {"email": "new_unique_email@example.com"}
        response = edit_email(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content.decode(), "Email edited succesfully")

        # Test invalid HTTP method
        request.method = 'GET'
        response = edit_email(request)
        self.assertEqual(response.status_code, 405)

    def test_delete_account(self):
        request = HttpRequest()

        # Test user authentication check
        request.method = 'POST'
        request.user = AnonymousUser()
        response = delete_account(request)
        self.assertEqual(response.status_code, 401)

        # Test delete_account successful case
        request.user = self.user
        with patch('mmapp.views.aws.s3_delete_folder') as mock_s3_delete_folder:
            response = delete_account(request)
            self.assertEqual(response.status_code, 200)
            mock_s3_delete_folder.assert_called()

        # Test invalid HTTP method
        request.method = 'GET'
        response = delete_account(request)
        self.assertEqual(response.status_code, 405)



from mmapp.views import search_results
class SearchViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        self.notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=self.user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )


    def test_search_results(self):
        request = HttpRequest()

        # Test user authentication check
        request.method = 'GET'
        request.user = AnonymousUser()
        response = search_results(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/')

        # Test search_results view without search_words parameter
        request.user = self.user
        response = search_results(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "search_results")

        # Test search_results view with notesonly and spellcheck in GET parameters
        request.GET = {
            "search_words": "test search",
            "notesonly": "on",
            "spellcheck": "on",
            "notebook": self.notebook.id,
        }
        with patch('mmapp.views.aws.search_on_ec2') as mock_search_on_ec2:
            mock_search_on_ec2.return_value = 'test_filename'
            with patch('mmapp.views.ml.load_embeddings') as mock_load_embeddings:
                mock_load_embeddings.return_value = {
                    'res_matrix': [],
                    'words': [],
                    'skipwords': [],
                    'spell_checked': [],
                }
                with patch('mmapp.views.sp.fruchterman_reingold') as mock_fruchterman_reingold:
                    mock_fruchterman_reingold.return_value = []
                    response = search_results(request)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "search_results")


        # Test search_results view with search_words parameter and mock search_on_ec2
        request.GET = {
            "search_words": "test search",
            "notebook": self.notebook.id,
        }
        with patch('mmapp.views.aws.search_on_ec2') as mock_search_on_ec2:
            mock_search_on_ec2.return_value = 'test_filename'
            with patch('mmapp.views.ml.load_embeddings') as mock_load_embeddings:
                mock_load_embeddings.return_value = {
                    'res_matrix': [],
                    'words': [],
                    'skipwords': [],
                    'spell_checked': [],
                }
                with patch('mmapp.views.sp.fruchterman_reingold') as mock_fruchterman_reingold:
                    mock_fruchterman_reingold.return_value = []
                    response = search_results(request)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "search_results")



    def test_inspect_node(self):
        request_factory = RequestFactory()
        request = request_factory.post(
            '/',
            content_type='application/json',
            data=json.dumps({
                'notebook_id': self.notebook.id,
                'searched_words': ['test', 'search'],
                'word': 'test'
            })
        )

        request.user = self.user

        # Test inspect_node view with mock inspect_on_ec2
        with patch('mmapp.views.aws.inspect_on_ec2') as mock_inspect_on_ec2:
            mock_inspect_on_ec2.return_value = ['test_result']
            response = inspect_node(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content), ['test_result'])

