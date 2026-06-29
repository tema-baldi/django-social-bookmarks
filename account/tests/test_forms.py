from django.template.backends import django
from django.test import TestCase
from account.forms import UserRegistrationForm, UserEditForm
from django.contrib.auth import get_user_model


User = get_user_model()


class UserRegistrationFormTest(TestCase):

    def test_password_mismatch(self):
        """Пароли не совпадают — форма невалидна."""
        form = UserRegistrationForm(data={'username': 'newuser', 'password': 'pass123', 'password2': 'different'})
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertEqual(form.errors['password2'][0],"Password don't match.")


    def test_password_match(self):
        """Пароли совпадают — валидация проходит."""
        form = UserRegistrationForm(data={'username': 'newuser', 'password': 'pass123', 'password2': 'pass123'})
        self.assertTrue(form.is_valid())


    def test_duplicate_email(self):
        """Email уже используется — форма невалидна."""
        User.objects.create_user(username='existing', email='dup@example.com', password='pass')
        form = UserRegistrationForm(data={'username': 'newuser',
                                          'password': 'pass123',
                                          'password2': 'pass123',
                                          'email': 'dup@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'Email already in use')


    def test_unique_email(self):
        """Новый email — форма валидна."""
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'email': 'unique@example.com',
            'password': 'pass123',
            'password2': 'pass123',
        })
        self.assertTrue(form.is_valid())


class UserEditFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass')
        cls.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass')


    def test_duplicate_email_user(self):
        """Email другого пользователя — ошибка."""
        form = UserEditForm(instance=self.user1, data={'email': self.user2.email})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'Email already in use.')


    def test_unique_email_edit(self):
        """Новый уникальный email — допустимо."""
        form = UserEditForm(instance=self.user1, data={'email': 'new@example.com'})
        self.assertTrue(form.is_valid())