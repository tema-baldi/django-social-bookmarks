from django.db.models import Model
from django.test import TestCase
from account.authentication import EmailAuthBackend, create_profile
from django.contrib.auth import get_user_model

from account.models import Profile

User = get_user_model()


class EmailAuthBackendTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.backend = EmailAuthBackend()
        cls.user = User.objects.create_user(username='user', password='password', email='test@mail.ru')


    def test_authenticate_with_valid_email(self):
        """Вход по email и правильному паролю."""
        test_user = self.backend.authenticate(request=None, username='test@mail.ru', password='password')
        self.assertEqual(test_user, self.user)


    def test_authenticate_with_wrong_password(self):
        """Вход с неправильным паролем."""
        test_user = self.backend.authenticate(request=None, username='test@mail.ru', password='wrong')
        self.assertIsNone(test_user)

    def test_authenticate_with_blank_fields(self):
        """Пустые поля не должны аутентифицировать."""
        test_user = self.backend.authenticate(request=None, username='', password='')
        self.assertIsNone(test_user)


    def test_get_user_id(self):
        """Получение пользователя по id"""
        user = self.backend.get_user(self.user.pk)
        self.assertEqual(user, self.user)


    def test_get_user_return_none_if_not_found(self):
        """Получение пользователя по несуществующему ID."""
        user = self.backend.get_user(123)
        self.assertIsNone(user)


    def test_get_user_with_invalid_id_type(self):
        """Передача невалидного ID (например, строки)."""
        user = self.backend.get_user('give_me_user_1')
        self.assertIsNone(user)


class CreateProfileTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='password', email='test@mail.ru')


    def test_create_profile_if_not_exists(self):
        """Создаёт профиль, если его нет."""
        # Убедимся что профиля нет
        Profile.objects.filter(user=self.user).delete()
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        # Создаем профиль и убеждается в том что он есть
        create_profile(backend=None, user=self.user)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())


    def test_dont_create_profile_if_exists(self):
        """Не создаёт дубликат профиля, если он уже есть."""
        Profile.objects.create(user=self.user)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        create_profile(backend=None, user=self.user)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)