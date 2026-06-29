from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from werkzeug.routing import ValidationError
from images.forms import ImageCreateForm
from images.models import Image

User = get_user_model()


class ImageCreateFormTest(TestCase):

    def test_clean_url_valid_extensions(self):
        """Допустимые расширения проходят валидацию."""
        valid_urls = ['http://example.com/image.jpg', 'http://example.com/image.jpeg', 'http://example.com/image.png']
        for url in valid_urls:
            form = ImageCreateForm(data={'title': 'Test', 'url': url, 'description': ''})
            self.assertTrue(form.is_valid(), f'Form should be valid for url {url}')


    def test_clean_url_invalid_extension(self):
        """Недопустимое расширение вызывает ошибку валидации."""
        form = ImageCreateForm(data={'title': 'Test', 'url': 'http://example.com/image.xxx', 'description': 'asd'})
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)
        self.assertEqual(form.errors['url'][0],'The given URL does not match valid image extensions.')


    def test_clean_url_missing_extension(self):
        """URL без расширения вызывает ошибку."""
        form = ImageCreateForm(data={'title': 'Test', 'url': 'http://example.com/image', 'description': 'asd'})
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)
        self.assertEqual(form.errors['url'][0], 'The given URL does not match valid image extensions.')

    @patch('images.forms.requests.get')
    def test_save_downloads_image(self, mock_get):
        """Метод save скачивает изображение по URL и сохраняет в поле image."""
        mock_response = MagicMock()
        mock_response.content = b'fake image content'
        mock_get.return_value = mock_response
        form_data = {
            'title': 'My Image',
            'url': 'http://example.com/image.jpg',
            'description': 'A nice image',
        }
        form = ImageCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        image = form.save(commit=False)
        mock_get.assert_called_once_with('http://example.com/image.jpg')
        self.assertTrue(image.image)
        expected_basename = slugify('My Image')
        self.assertIn(expected_basename, image.image.name)
        self.assertTrue(image.image.name.endswith('.jpg'))
        self.assertEqual(image.image.read(), b'fake image content')

    @patch('images.forms.requests.get')
    def test_save_with_commit_true(self, mock_get):
        """Сохранение с commit=True создаёт объект в БД."""
        mock_response = MagicMock()
        mock_response.content = b'fake image content'
        mock_get.return_value = mock_response
        user = User.objects.create_user(username='testuser', password='pass')
        form = ImageCreateForm(data={
            'title': 'Commit Test',
            'url': 'http://example.com/image.jpg',
            'description': '',
        })
        self.assertTrue(form.is_valid())
        image = form.save(commit=False)
        image.user = user
        image.save()
        self.assertTrue(Image.objects.filter(title='Commit Test').exists())
        saved_image = Image.objects.get(title='Commit Test')
        self.assertTrue(saved_image.image.name.endswith('.jpg'))
        self.assertGreater(saved_image.image.size, 0)