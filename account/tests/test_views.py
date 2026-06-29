from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.api import get_messages
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from account.models import Profile, Contact
from actions.models import Action


User = get_user_model()


class DashboardViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='password')
        cls.profile = Profile.objects.create(user=cls.user)


    def test_dashboard_required_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f'/account/login/?next={reverse("dashboard")}')


    def test_dashboard_authenticate(self):
        """Авторизованный пользователь видит дашборд."""
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/dashboard.html')



    def test_dashboard_context_contains_actions(self):
        """В контексте передаются действия (actions)."""
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertIn('actions', response.context)


    def test_dashboard_shows_only_followed_actions(self):
        """Показываются только действия пользователей, на которых подписан текущий."""
        user2 = User.objects.create_user(username='user2', password='pass2')
        Profile.objects.create(user=user2)
        action = Action.objects.create(user=user2, verb='test action')
        Contact.objects.create(user_from=self.user, user_to=user2)
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('dashboard'))
        actions = response.context['actions']
        self.assertIn(action, actions)


    def test_dashboard_excludes_own_actions(self):
        """Действия текущего пользователя не отображаются."""
        Action.objects.create(user=self.user, verb='test my_action')
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('dashboard'))
        actions = response.context['actions']
        self.assertEqual(actions.count(), 0)


class RegisterViewTest(TestCase):

    def test_register_get(self):
        """GET-запрос отображает форму регистрации."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register.html')
        self.assertIn('form', response.context)


    def test_register_post_valid(self):
        """Успешная регистрация создаёт пользователя, профиль и действие."""
        data = {
            'username': 'newuser',
            'first_name': 'John',
            'email': 'john@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register_done.html')
        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(Action.objects.filter(user=user, verb='has created an account').exists())


    def test_register_with_invalid_data(self):
        """Невалидные данные не создают пользователя."""
        data = {
            'username': 'newuser',
            'password': 'testpass123',
            'password2': 'different',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register.html')
        self.assertFalse(User.objects.filter(username='newuser').exists())
        self.assertIn('form', response.context)


class EditViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='pass')
        Profile.objects.create(user=cls.user)


    def test_edit_required_login(self):
        """Анонимный доступ запрещён."""
        response = self.client.get(reverse('edit'))
        self.assertRedirects(response, f'/account/login/?next={reverse("edit")}')


    def test_edit_get(self):
        """GET-запрос показывает формы с текущими данными."""
        self.client.login(username='testuser', password='pass')
        response = self.client.get(reverse('edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/edit.html')
        self.assertEqual(response.context['user_form'].instance, self.user)
        self.assertEqual(response.context['profile_form'].instance, self.user.profile)

    def test_edit_post_valid(self):
        """Валидные данные обновляют профиль и показывают сообщение об успехе."""
        self.client.login(username='testuser', password='pass')
        data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com',
            'date_of_birth': '1995-05-05',
        }
        response = self.client.post(reverse('edit'), data)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.date_of_birth.strftime('%Y-%m-%d'), '1995-05-05')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Profile updated!!!' in str(m) for m in messages))


    def test_edit_post_invalid(self):
        """Невалидные данные показывают форму с ошибками и сообщение об ошибке."""
        self.client.login(username='testuser', password='pass')
        data = {
            'email': 'invalid-email',
            'date_of_birth': 'invalid-date',
        }
        response = self.client.post(reverse('edit'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/edit.html')
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Error updating your profile' in str(m) for m in messages))


class UserListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.active_user = User.objects.create_user(username='active', password='pass', is_active=True)
        cls.inactive_user = User.objects.create_user(username='inactive', password='pass', is_active=False)


    def test_user_list_requires_login(self):
        """Анонимный доступ запрещён."""
        response = self.client.get(reverse('user_list'))
        self.assertRedirects(response, f'/account/login/?next={reverse("user_list")}')


    def test_user_list_shows_only_active(self):
        """Отображаются только активные пользователи."""
        self.client.login(username='active', password='pass')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/user/list.html')
        users = response.context['users']
        self.assertIn(self.active_user, users)
        self.assertNotIn(self.inactive_user, users)


class UserDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='pass')
        Profile.objects.create(user=cls.user)


    def test_user_detail_requires_login(self):
        """Анонимный доступ запрещён."""
        response = self.client.get(reverse('user_detail', args=['user']))
        self.assertRedirects(response, f'/account/login/?next={reverse("user_detail", args=["user"])}')


    def test_user_detail_found(self):
        """Активный пользователь отображается корректно."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('user_detail', args=['user']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/user/detail.html')
        self.assertEqual(response.context['user'], self.user)


    def test_user_detail_404_if_not_exist(self):
        """Несуществующий пользователь возвращает 404."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('user_detail', args=['404user']))
        self.assertEqual(response.status_code, 404)


class UserFollowViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1', password='pass')
        cls.user2 = User.objects.create_user(username='user2', password='pass')


    def test_follow_required_login(self):
        """Анонимный доступ запрещён."""
        response = self.client.post(reverse('user_follow'), {'id': self.user2.id, 'action': 'follow'})
        self.assertRedirects(response, f'/account/login/?next={reverse("user_follow")}')


    def test_follow_user(self):
        """Подписка создаёт связь и действие."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('user_follow'), {'id': self.user2.id, 'action': 'follow'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'ok'})
        self.assertTrue(Contact.objects.filter(user_from=self.user1, user_to=self.user2).exists())
        target_ct = ContentType.objects.get_for_model(self.user2)
        self.assertTrue(Action.objects.filter(user=self.user1, verb='is following', target_ct=target_ct, target_id=self.user2.id).exists())


    def test_unfollow_user(self):
        """Отписка удаляет связь."""
        Contact.objects.create(user_from=self.user1, user_to=self.user2)
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('user_follow'), {'id': self.user2.id, 'action': 'unfollow'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'ok'})
        self.assertFalse(Contact.objects.filter(user_from=self.user1, user_to=self.user2).exists())


    def test_follow_nonexistent_user(self):
        """Попытка подписаться на несуществующего пользователя возвращает ошибку."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('user_follow'), {'id': 123, 'action': 'follow'})
        self.assertJSONEqual(response.content, {'status': 'error'})


    def test_follow_missing_params(self):
        """Отсутствие параметров возвращает ошибку."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('user_follow'), {})
        self.assertJSONEqual(response.content, {'status': 'error'})


