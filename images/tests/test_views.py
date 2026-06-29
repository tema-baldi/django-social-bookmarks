import json
from unittest.mock import patch, MagicMock

from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.api import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Model
from django.test import TestCase
from django.urls import reverse

from actions.models import Action
from images.models import Image
from django.contrib.auth import get_user_model

User = get_user_model()


class ImageCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='pass')


    def test_image_create_requires_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(reverse('images:create'))
        self.assertRedirects(response, f'/account/login/?next={reverse("images:create")}')


    def test_image_create_get_with_initial_data(self):
        """GET с параметрами title и url показывает форму с предзаполненными данными."""
        self.client.login(username='user', password='pass')
        url = reverse('images:create')
        data = {'title': 'Test', 'url': 'http://example.com/img.jpg'}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/create.html')
        self.assertEqual(response.context['form'].data['title'], 'Test')
        self.assertEqual(response.context['form'].data['url'], 'http://example.com/img.jpg')

    @patch('images.views.r.incr')
    @patch('images.views.r.zincrby')
    @patch('images.forms.requests.get')
    def test_image_create_post_valid(self, mock_get, mock_zincrby, mock_incr):
        """Успешное создание изображения."""
        self.client.login(username='user', password='pass')
        mock_response = MagicMock()
        mock_response.content = b'fake image content'
        mock_get.return_value = mock_response
        data = {
            'title': 'My Image',
            'url': 'http://example.com/img.jpg',
            'description': 'A nice image',
        }
        response = self.client.post(reverse('images:create'), data)
        self.assertEqual(response.status_code, 302)
        image = Image.objects.get(title='My Image')
        self.assertEqual(image.user, self.user)
        self.assertRedirects(response, image.get_absolute_url())
        target_ct = ContentType.objects.get_for_model(image)
        self.assertTrue(Action.objects.filter(user=self.user, verb='bookmarked image', target_ct=target_ct,
                                              target_id=image.pk).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Image added successfully!' in str(m) for m in messages))

    def test_image_create_post_invalid_url(self):
        """Невалидный URL (не изображение)."""
        self.client.login(username='user', password='pass')
        data = {
            'title': 'Invalid',
            'url': 'http://example.com/file.txt',
        }
        response = self.client.post(reverse('images:create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/create.html')
        self.assertIn('url', response.context['form'].errors)
        self.assertFalse(Image.objects.filter(title='Invalid').exists())


class ImageDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='pass')
        cls.image = Image.objects.create(
            user=cls.user,
            title='Detail Image',
            slug='detail-image',
            url='http://example.com/img.jpg',
            image=SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        )

    @patch('images.views.r.incr')
    @patch('images.views.r.zincrby')
    def test_image_detail(self, mock_zincrby, mock_incr):
        """Детальная страница увеличивает счётчики."""
        mock_incr.return_value = 5
        response = self.client.get(self.image.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/detail.html')
        self.assertEqual(response.context['image'], self.image)
        self.assertEqual(response.context['total_views'], 5)
        mock_incr.assert_called_once_with(f'image:{self.image.id}:views')
        mock_zincrby.assert_called_once_with('image_ranking', 1, self.image.id)

    def test_image_detail_404(self):
        """Несуществующее изображение возвращает 404."""
        response = self.client.get(reverse('images:detail', args=[999, 'nonexistent']))
        self.assertEqual(response.status_code, 404)


class ImageLikeViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1', password='pass')
        cls.user2 = User.objects.create_user(username='user2', password='pass')
        cls.image = Image.objects.create(
            user=cls.user2,
            title='Likeable Image',
            slug='likeable',
            url='http://example.com/img.jpg',
            image=SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg"))


    def test_image_create_requires_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.post(reverse('images:like'), {'id': self.image.id, 'action': 'like'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, f'/account/login/?next={reverse("images:like")}')

    def test_image_like(self):
        """Добавление лайка."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('images:like'), {'id': self.image.id, 'action': 'like'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(self.image.users_like.filter(id=self.user1.id).exists())
        target_ct = ContentType.objects.get_for_model(self.image)
        self.assertTrue(Action.objects.filter(user=self.user1, verb='likes', target_ct=target_ct, target_id=self.image.pk).exists())

    def test_image_unlike(self):
        """Удаление лайка."""
        self.client.login(username='user1', password='pass')
        self.image.users_like.add(self.user1)
        response = self.client.post(reverse('images:like'), {'id': self.image.id, 'action': 'unlike'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertFalse(self.image.users_like.filter(id=self.user1.id).exists())

    def test_image_like_missing_params(self):
        """Отсутствуют параметры."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('images:like'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')

    def test_image_like_invalid_id(self):
        """Несуществующее изображение."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('images:like'), {'id': 999, 'action': 'like'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')

    def test_image_like_requires_post(self):
        """GET-запрос к image_like возвращает 405 Method Not Allowed."""
        self.client.login(username='user1', password='pass')
        response = self.client.get(reverse('images:like'), {'id': 999, 'action': 'like'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 405)


class ImageListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='pass')
        for i in range(10):
            Image.objects.create(
                user=cls.user,
                title=f'Image {i}',
                slug=f'image-{i}',
                url=f'http://example.com/img{i}.jpg',
                image=SimpleUploadedFile(f'{i}.jpg', b'content', content_type='image/jpeg')
            )

    def test_image_list_requires_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(reverse('images:list'))
        self.assertRedirects(response, f'/account/login/?next={reverse("images:list")}')

    def test_image_list_first_page(self):
        """Первая страница показывает 8 изображений."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/list.html')
        self.assertEqual(len(response.context['images']), 8)
        self.assertEqual(response.context['section'], 'images')

    def test_image_list_second_page(self):
        """Вторая страница показывает оставшиеся 2 изображения."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:list'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['images']), 2)

    def test_image_list_ajax(self):
        """AJAX-запрос с images_only возвращает только HTML-фрагмент."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:list'), {'page': 1, 'images_only': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/list_images.html')
        self.assertContains(response, '<div class="image"')

    def test_image_list_empty_page_with_images_only(self):
        """Запрос страницы вне диапазона с images_only возвращает пустую строку."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:list'), {'page': 1111, 'images_only': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '')

    def test_image_list_page_not_integer(self):
        """Нецелое значение page возвращает первую страницу."""
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:list'), {'page': 'asd', 'images_only': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['images']), 8)
        self.assertEqual(response.context['images'].number, 1)


class ImageRankingViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='pass')
        # Создаём несколько изображений
        cls.images = []
        for i in range(5):
            img = Image.objects.create(
                user=cls.user,
                title=f'Rank {i}',
                slug=f'rank-{i}',
                url=f'http://example.com/rank{i}.jpg',
                image=SimpleUploadedFile(f'rank{i}.jpg', b'content', content_type='image/jpeg')
            )
            cls.images.append(img)

    def test_image_ranking_requires_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(reverse('images:ranking'))
        self.assertRedirects(response, f'/account/login/?next={reverse("images:ranking")}')

    @patch('images.views.r.zrange')
    def test_image_ranking(self, mock_zrange):
        """Рейтинг возвращает топ-10 изображений на основе Redis."""
        mock_zrange.return_value = [b'4', b'2', b'1']
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:ranking'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/ranking.html')
        most_viewed = response.context['most_viewed']
        expected_ids = [4, 2, 1]
        self.assertEqual([img.id for img in most_viewed], expected_ids)
        self.assertEqual(response.context['section'], 'images')

    @patch('images.views.r.zrange')
    def test_image_ranking_empty(self, mock_zrange):
        """Рейтинг с пустым результатом."""
        mock_zrange.return_value = []
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('images:ranking'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['most_viewed'], [])
