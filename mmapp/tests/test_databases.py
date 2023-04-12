from django.test import TestCase
from ..models import Note, Notebook, User

class test_databases(TestCase):
    ''' Tests for Django databases '''
    def test_user(self):
        ''' Test user objects.

        Requirements:
            FR#1 -- Request.Registration
            FR#2 -- Delete.Account
        '''
        user = User.objects.create_user(
            username="testuser1",
            email="testemail1@email.com",
            password="testpassword1"
        )
        user.save()
        user = User.objects.get(username="testuser1")
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "testemail1@email.com")
        user = User.objects.get(email="testemail1@email.com")
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "testuser1")

        user.delete()
        self.assertRaises(User.DoesNotExist, User.objects.get, username="testuser1")
        self.assertRaises(User.DoesNotExist, User.objects.get, email="testemail1@email.com")
        self.assertRaises(Notebook.DoesNotExist, Notebook.objects.get, owner=user)
        self.assertRaises(Note.DoesNotExist, Note.objects.get, owner=user)

    def test_notebook(self):
        ''' Test notebook objects.

        Requirements:
            FR#8 -- Create.Notebook
            FR#9 -- Edit.Notebook
            FR#10 -- Delete.Notebook
            FR#11 -- Merge.Notebook
        '''
        user = User.objects.create_user(
            username="testuser2",
            email="testemail2@email.com",
            password="testpassword2"
        )
        user.save()
        notebook = Notebook.objects.create(
            name='testnotebook2',
            owner=user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )
        notebook.save()
        notebook = Notebook.objects.get(name="testnotebook2")
        self.assertIsInstance(notebook, Notebook)
        self.assertEqual(notebook.name, "testnotebook2")

        notebook.delete()
        self.assertRaises(Note.DoesNotExist, Note.objects.get, file_name="testnote2")
        self.assertRaises(Notebook.DoesNotExist, Notebook.objects.get, name="testnotebook2")

        user.delete()

    def test_note(self):
        ''' Test note objects.

        Requirements:
            FR#7 -- Upload.Notes
            FR#9 -- Edit.Notebook
        '''
        user = User.objects.create_user(
            username="testuser3",
            email="testemail3@email.com",
            password="testpassword3"
        )
        user.save()
        notebook = Notebook.objects.create(
            name='testnotebook3',
            owner=user,
            vocab='vocab',
            corpus='corpus',
            kv='kv',
            kv_vectors='kv_v'
        )
        notebook.save()
        note = Note.objects.create(
            file_name='testnote3',
            file_type='text/plain',
            owner=user,
            notebooks=notebook,
            vocab='vocab',
            corpus='corpus'
        )
        note.save()

        note = Note.objects.get(file_name='testnote3')
        self.assertIsInstance(note, Note)
        self.assertEqual(note.file_type, 'text/plain')
        self.assertEqual(note.owner, user)
        self.assertEqual(note.notebooks, notebook)
        self.assertEqual(note.vocab, 'vocab')
        self.assertEqual(note.corpus, 'corpus')
        self.assertIsNotNone(Notebook.objects.filter(notes=note))

        note.delete()
        self.assertRaises(Note.DoesNotExist, Note.objects.get, file_name="testnote3")
        notebook = Notebook.objects.get(name='testnotebook3')
        self.assertRaises(Note.DoesNotExist, notebook.notes.get, file_name="testnote3")

        notebook.delete()
        user.delete()
        