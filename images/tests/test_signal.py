from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from images.models import Image


User = get_user_model()


class ImageSignalTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1', password='pass')
        cls.user2 = User.objects.create_user(username='user2', password='pass')
        cls.image = Image.objects.create(
            user=cls.user1,
            title='Test Image',
            slug='test-image',
            url='http://example.com/img.jpg',
            image=SimpleUploadedFile('test.jpg', b'content', content_type='image/jpeg')
        )


    def test_total_likes_increases_on_like_add(self):
        """Добавление лайка увеличивает total_likes."""
        self.assertEqual(self.image.total_likes, 0)
        self.image.users_like.add(self.user2)
        self.image.refresh_from_db()
        self.assertEqual(self.image.total_likes, 1)

    def test_total_likes_decreases_on_like_remove(self):
        """Удаление лайка уменьшает total_likes."""
        self.image.users_like.add(self.user1)
        self.image.refresh_from_db()
        self.assertEqual(self.image.total_likes, 1)
        self.image.users_like.remove(self.user1)
        self.image.refresh_from_db()
        self.assertEqual(self.image.total_likes, 0)

    def test_total_likes_after_multiple_likes(self):
        """Несколько лайков правильно обновляют total_likes."""
        self.image.users_like.add(self.user1, self.user2)
        self.image.refresh_from_db()
        self.assertEqual(self.image.total_likes, 2)

    def test_total_likes_after_clear(self):
        """Очистка всех лайков обнуляет total_likes."""
        self.image.users_like.add(self.user1, self.user2)
        self.image.refresh_from_db()
        self.assertEqual(self.image.total_likes, 2)
        self.image.users_like.clear()
        self.image.refresh_from_db()
        self.assertEqual(self.image.total_likes, 0)
