from datetime import timedelta
from django.utils.timezone import now
from django.test import TestCase
from voting.models import User, Competition, Participant, Vote, Comment
from voting.forms import CustomUserCreationForm, CompetitionForm, ParticipantForm
from django.urls import reverse

class CustomUserManagerTestCase(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="password123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,
                first_name="Test",
                last_name="User",
                password="password123"
            )

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="password123"
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_create_superuser_invalid_flags(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                password="password123",
                is_superuser=False
            )


class CompetitionModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            first_name="Owner",
            last_name="User",
            password="password123"
        )

    def test_competition_status_update(self):
        competition = Competition.objects.create(
            title="Test Competition",
            description="A test competition.",
            start_date=now() + timedelta(days=1),
            end_date=now() + timedelta(days=2),
            owner=self.user
        )
        self.assertEqual(competition.status, "available")

        competition.start_date = now() - timedelta(days=1)
        competition.end_date = now() + timedelta(days=1)
        competition.save()
        self.assertEqual(competition.status, "voting")

        competition.start_date = now() - timedelta(days=2)
        competition.end_date = now() - timedelta(days=1)
        competition.save()
        self.assertEqual(competition.status, "completed")


class ParticipantModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="participant@example.com",
            first_name="Participant",
            last_name="User",
            password="password123"
        )
        self.competition = Competition.objects.create(
            title="Competition",
            description="A test competition.",
            start_date=now(),
            end_date=now() + timedelta(days=1),
            owner=self.user
        )

    def test_participant_creation(self):
        participant = Participant.objects.create(
            user=self.user,
            competition=self.competition,
            title="Participant Title",
            description="Participant Description"
        )
        self.assertEqual(participant.title, "Participant Title")
        self.assertEqual(participant.competition, self.competition)


class VoteModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="voter@example.com",
            first_name="Voter",
            last_name="User",
            password="password123"
        )
        self.competition = Competition.objects.create(
            title="Competition",
            description="A test competition.",
            start_date=now(),
            end_date=now() + timedelta(days=1),
            owner=self.user
        )
        self.participant = Participant.objects.create(
            user=self.user,
            competition=self.competition,
            title="Participant Title",
            description="Participant Description"
        )

    def test_vote_unique_constraint(self):
        Vote.objects.create(
            competition=self.competition,
            voter=self.user,
            participant=self.participant
        )
        with self.assertRaises(Exception):  # Expecting IntegrityError or similar
            Vote.objects.create(
                competition=self.competition,
                voter=self.user,
                participant=self.participant
            )


class CommentModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="commenter@example.com",
            first_name="Commenter",
            last_name="User",
            password="password123"
        )
        self.competition = Competition.objects.create(
            title="Competition",
            description="A test competition.",
            start_date=now(),
            end_date=now() + timedelta(days=1),
            owner=self.user
        )

    def test_comment_creation(self):
        comment = Comment.objects.create(
            user=self.user,
            competition=self.competition,
            text="This is a test comment."
        )
        self.assertEqual(comment.text, "This is a test comment.")
        self.assertFalse(comment.is_deleted)

class ViewsTestCase(TestCase):
    def setUp(self):
        # Create user and assign it to self.user
        self.user = User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="password123"
        )
        self.client.login(email='test@example.com', password='password123')

        self.competition = Competition.objects.create(
            title="Test Competition",
            description="Test Description",
            start_date=now() + timedelta(days=1),
            end_date=now() + timedelta(days=2),
            voting_type="single_choice",
            owner=self.user,
        )

        self.participant = Participant.objects.create(
            competition=self.competition,
            user=self.user,
            title="Test Participant",
            description="Participant Description",
        )

        self.comment = Comment.objects.create(
            competition=self.competition,
            user=self.user,
            text="Test Comment",
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_all_competitions_view(self):
        response = self.client.get(reverse('all_competitions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_competitions.html')
        self.assertContains(response, "Test Competition")

    def test_create_competition_view(self):
        response = self.client.post(reverse('create_competition'), {
            'title': 'New Competition',
            'description': 'Description of new competition',
            'start_date': '2024-12-06 12:00:00',
            'end_date': '2024-12-07 12:00:00',
            'voting_type': 'single_choice',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Competition.objects.filter(title='New Competition').exists())

    def test_my_competition_detail_view(self):
        url = reverse('my_competition_detail', args=[self.competition.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_competition_detail.html')
        self.assertContains(response, "Test Competition")

    def test_competition_detail_view(self):
        url = reverse('competition_detail', args=[self.competition.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'competition_detail.html')
        self.assertContains(response, "Test Competition")

    def test_delete_participant_view(self):
        url = reverse('delete_participant', args=[self.competition.id, self.participant.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Participant.objects.filter(id=self.participant.id).exists())

    def test_delete_comment_view(self):
        url = reverse('delete_comment', args=[self.competition.id, self.comment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_competition_results_view(self):
        url = reverse('competition_results', args=[self.competition.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'competition_results.html')

class CustomUserCreationFormTestCase(TestCase):
    def test_invalid_password_mismatch(self):
        form = CustomUserCreationForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'password123',
            'password2': 'differentpassword',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_missing_email(self):
        form = CustomUserCreationForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'password123',
            'password2': 'password123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class CompetitionFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            first_name="Owner",
            last_name="User",
            password="password123"
        )

    def test_start_date_in_past(self):
        form = CompetitionForm(data={
            'title': 'Test Competition',
            'description': 'A test competition.',
            'start_date': now() - timedelta(days=1),
            'end_date': now() + timedelta(days=2),
            'voting_type': 'single_choice',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_end_date_before_start_date(self):
        form = CompetitionForm(data={
            'title': 'Test Competition',
            'description': 'A test competition.',
            'start_date': now() + timedelta(days=1),
            'end_date': now(),
            'voting_type': 'single_choice',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)