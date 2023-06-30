from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Иван Иванов')
        cls.reader = User.objects.create(username='Петр Петров')
        cls.list_url = reverse('notes:list')
        cls.note = Note.objects.create(
            title='Заголовок',
            author=cls.author,
            text='Текст комментария',
        )

    def test_note_in_list_for_author(self):
        self.client.force_login(self.author)
        response = self.client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_another_user(self):
        self.client.force_login(self.reader)
        response = self.client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_pages_contains_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
