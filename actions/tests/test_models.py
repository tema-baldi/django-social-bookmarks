from django.contrib.admin import action
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from actions.models import Action
from django.contrib.auth import get_user_model


User = get_user_model()


class ActionModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='pass')
        cls.target_user = User.objects.create_user(username='targetuser', password='pass')


    def test_action_without_target(self):
        """Действие без целевого объекта."""
        action = Action.objects.create(user=self.user, verb='logged in')
        self.assertEqual(action.user, self.user)
        self.assertEqual(action.verb, 'logged in')
        self.assertIsNone(action.target)
        self.assertIsNotNone(action.created)


    def test_action_with_taget(self):
        """Действие с целевым объектом (GenericForeignKey)."""
        action = Action.objects.create(user=self.user, verb='followed', target=self.target_user)
        self.assertEqual(action.user, self.user)
        self.assertEqual(action.verb, 'followed')
        self.assertEqual(action.target, self.target_user)
        target_ct = ContentType.objects.get_for_model(self.target_user)
        self.assertEqual(target_ct, action.target_ct)
        self.assertEqual(action.target_id, self.target_user.id)
