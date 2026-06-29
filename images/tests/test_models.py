from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from images.models import Image
from django.contrib.auth import get_user_model

User = get_user_model()


class ImageTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='pass')
        cls.test_image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')

    def test_create_image_without_slug(self):
        """Slug генерируется автоматически из title."""
        image = Image.objects.create(user=self.user,
                                     title='Test Image Title',
                                     url='http://example.com/img.jpg',
                                     image=self.test_image)
        self.assertEqual(image.slug, 'test-image-title')


    def test_create_image_with_slug(self):
        """Переданный slug сохраняется."""
        image = Image.objects.create(user=self.user,
                                     title='Test Image Title',
                                     slug='test-slug',
                                     url='http://example.com/img.jpg',
                                     image=self.test_image)
        self.assertEqual(image.slug, 'test-slug')


    def test_image_str(self):
        """Строковое представление возвращает title."""
        image = Image.objects.create(user=self.user,
                                     title='Test Image Title',
                                     url='http://example.com/img.jpg',
                                     image=self.test_image)
        self.assertEqual(str(image), 'Test Image Title')


    def test_get_absolute_url(self):
        image = Image.objects.create(user=self.user,
                                     title='Test Image Title',
                                     url='http://example.com/img.jpg',
                                     image=self.test_image)
        expected_url = reverse('images:detail', args=[image.pk, image.slug])
        self.assertEqual(expected_url, image.get_absolute_url())