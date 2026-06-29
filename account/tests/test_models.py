from django.contrib.auth import get_user_model
from django.test import TestCase
from account.models import Profile, Contact


# возвращает модель, указанную в AUTH_USER_MODEL (по умолчанию django.contrib.auth.models.User)
User = get_user_model()

class ProfileModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test_user', password='test_pass')

    def test_profile_str(self):
        """Строковое представление профиля."""
        Profile.objects.create(user=self.user)
        self.assertEqual(str(self.user.profile), 'Profile of test_user')


class ContactModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='test_user1', password='test_pass1')
        cls.user2 = User.objects.create_user(username='test_user2', password='test_pass2')

    def test_contact_str(self):
        """Строковое представление профиля."""
        contact = Contact.objects.create(user_to=self.user1, user_from=self.user2)
        self.assertEqual(str(contact), 'test_user2 follows test_user1')


class UserFollowingFieldTest(TestCase):
    def test_user_has_following_field(self):
        """Поле following динамически добавлено к модели User."""
        user = User.objects.create_user(username='test_user', password='test_pass')
        self.assertTrue(hasattr(user, 'following'))

    def test_follow_relationship(self):
        """Подписка работает через промежуточную модель Contact."""
        user1 = User.objects.create_user(username='test_user1', password='test_pass1')
        user2 = User.objects.create_user(username='test_user2', password='test_pass2')
        user1.following.add(user2)

        # Проверяем, что связь создалась
        self.assertTrue(Contact.objects.filter(user_from=user1, user_to=user2).exists())

        # Проверяем обратную связь (подписчики)
        self.assertTrue(user2.followers.filter(pk=user1.pk).exists())

        # Отписаться
        user1.following.remove(user2)
        self.assertFalse(Contact.objects.filter(user_from=user1, user_to=user2).exists())

