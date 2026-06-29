from django.test import TestCase
from django.utils import timezone
from actions.models import Action
from actions.utils import create_action
from django.contrib.auth import get_user_model
from datetime import timedelta


User = get_user_model()


class CreateActionTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='pass')
        cls.target_user = User.objects.create_user(username='target', password='pass')


    def test_create_action_without_target(self):
        """Создание действия без целевого объекта."""
        res = create_action(self.user, verb='login')
        self.assertTrue(res)
        self.assertEqual(Action.objects.count(), 1)
        action = Action.objects.first()
        self.assertEqual(action.user, self.user)
        self.assertEqual(action.verb, 'login')
        self.assertIsNone(action.target)


    def test_create_action_with_target(self):
        """Создание действия с целевым объектом."""
        res = create_action(self.user, verb='followed', target=self.target_user)
        self.assertTrue(res)
        self.assertEqual(Action.objects.count(), 1)
        action = Action.objects.first()
        self.assertEqual(action.target, self.target_user)


    def test_duplicate_action_ignored_within_60_seconds(self):
        """Повторное действие в течение 60 секунд не создаётся."""
        create_action(self.user, 'liked', self.target_user)
        res = create_action(self.user, 'liked', self.target_user)
        self.assertFalse(res)
        self.assertEqual(Action.objects.count(), 1)


    def test_duplicate_action_after_60_seconds(self):
        """Действие повторяется, если прошло больше 60 секунд."""
        create_action(self.user, 'liked', self.target_user)
        action = Action.objects.first()
        action.created = timezone.now() - timedelta(seconds=61)
        action.save()
        res = create_action(self.user, 'liked', self.target_user)
        self.assertTrue(res)
        self.assertEqual(Action.objects.count(), 2)


    def test_same_verb_different_target_creates_new(self):
        """Действие с тем же глаголом, но другим объектом, создаётся."""
        user2 = User.objects.create_user(username='user2', password='pass')
        create_action(self.user, 'followed', self.target_user)
        res = create_action(user2, 'followed', self.target_user)
        self.assertTrue(res)
        self.assertEqual(Action.objects.count(), 2)