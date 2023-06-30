from django.contrib.auth import get_user_model
from django.urls import reverse
from notes.models import Note
from django.test import Client, TestCase
from notes.forms import WARNING
from pytils.translit import slugify
from http import HTTPStatus


User = get_user_model()


class TestLogin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Иван Иванов')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.form_data = {'title': 'Новый заголовок',
                         'text': 'Новый текст',
                         'slug': 'novyi-slug'}
        cls.done_url = reverse('notes:success')

    def test_anonymous_user_cant_create_comment(self):
        self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_can_create_comment(self):

        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.slug, self.form_data['slug'])


class TestSlug(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Иван Иванов')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.note = Note.objects.create(
            title='Заголовок',
            author=cls.user,
            text='Текст комментария',
            slug='slug',
        )
        cls.form_data = {'title': 'Новый заголовок',
                         'text': 'Новый текст',
                         'slug': 'slug'}
        cls.done_url = reverse('notes:success')

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )


class TestEmptySlug(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Иван Иванов')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.form_data = {'title': 'Новый заголовок',
                         'text': 'Новый текст',
                         'slug': 'slug'}
        cls.done_url = reverse('notes:success')

    def test_empty_slug(self):
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestAuthorEditNote(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Иван Иванов')
        cls.reader = User.objects.create(username='Петр Петров')
        cls.auth_client = Client()
        cls.note = Note.objects.create(
             title='Заголовок',
             author=cls.author,
             text='Текст комментария',
             slug='slug',
             )
        cls.url = reverse('notes:edit', args=(cls.note.slug,))
        cls.form_data = {'title': 'Новый заголовок',
                         'text': 'Новый текст',
                         'slug': 'novyi-slug'}
        cls.done_url = reverse('notes:success')

    def test_author_can_edit_note(self):
        self.auth_client.force_login(self.author)
        response = self.auth_client.post(self.url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.reader)
        response = self.client.post(self.url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
