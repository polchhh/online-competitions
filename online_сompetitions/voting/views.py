from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Competition,  Participant, Comment, Vote
from .forms import CustomUserCreationForm, CompetitionForm, ParticipantForm
from datetime import datetime
from django.utils.timezone import make_aware
from django.db.models import Count
from django.contrib import messages

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user) 
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user) 
            return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def all_competitions(request):
    filter_by = request.GET.get('filter', 'all') 
    competitions = Competition.objects.all()

    for competition in competitions:
        competition.update_status()

    if filter_by == 'available':
        competitions = [c for c in competitions if c.status == 'available']
    elif filter_by == 'voting':
        competitions = [c for c in competitions if c.status == 'voting']
    elif filter_by == 'completed':
        competitions = [c for c in competitions if c.status == 'completed']

    return render(request, 'all_competitions.html', {'competitions': competitions})


@login_required
def create_competition(request):
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():
            competition = form.save(commit=False)
            competition.owner = request.user 
            competition.save()
            return redirect('competition_detail', id=competition.id)
    else:
        form = CompetitionForm()

    return render(request, 'create_competition.html', {'form': form})

@login_required
def my_competition_detail(request, id):
    competition = get_object_or_404(Competition, id=id)

    if competition.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете просматривать этот конкурс.")
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        voting_type = request.POST.get('voting_type')

        try:
            start_date = make_aware(datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')) if start_date_str else None
            end_date = make_aware(datetime.strptime(end_date_str, '%Y-%m-%d %H:%M')) if end_date_str else None

            competition.title = title
            competition.description = description
            competition.start_date = start_date if start_date else competition.start_date 
            competition.end_date = end_date if end_date else competition.end_date
            competition.voting_type = voting_type
            competition.save()

            messages.success(request, "Изменения успешно сохранены.")
            return redirect('my_competition_detail', id=competition.id)
        except ValueError:
            messages.error(request, "Неверный формат даты. Пожалуйста, используйте 'ГГГГ-ММ-ДД ЧЧ:ММ'.")

    participants = competition.participants.all()
    comments = competition.comments.filter(is_deleted=False)

    return render(request, 'my_competition_detail.html', {
        'competition': competition,
        'participants': participants,
        'comments': comments,
    })

@login_required
def competition_detail(request, id):
    competition = get_object_or_404(Competition, id=id)
    participants = competition.participants.all()
    user_participation = competition.participants.filter(user=request.user).exists()
    comments = competition.comments.filter(is_deleted=False)

    competition.update_status()

    user_votes = Vote.objects.filter(competition=competition, voter=request.user)
    voted_participant_ids = [vote.participant.id for vote in user_votes]
    voted_participants = competition.participants.filter(id__in=voted_participant_ids)


    if request.method == 'POST' and 'vote' in request.POST:
        participant_ids = request.POST.getlist('participants') 

        if competition.voting_type == 'multiple_choice':
            new_votes = []
            for participant_id in participant_ids:
                if int(participant_id) not in voted_participant_ids:
                    participant = get_object_or_404(Participant, id=participant_id)
                    new_votes.append(Vote(competition=competition, voter=request.user, participant=participant))
            Vote.objects.bulk_create(new_votes)
        else: 
            participant_id = int(participant_ids[0])
            if participant_id not in voted_participant_ids:
                participant = get_object_or_404(Participant, id=participant_id)
                Vote.objects.create(competition=competition, voter=request.user, participant=participant)

        return redirect('competition_detail', id=id)

    if request.method == 'POST' and 'apply' in request.POST:
        if competition.status == 'available':
            title = request.POST.get('title')
            description = request.POST.get('description')
            Participant.objects.create(competition=competition, user=request.user, title=title, description=description)
        return redirect('competition_detail', id=id)

    if request.method == 'POST' and 'comment' in request.POST:
        comment_text = request.POST.get('comment')
        Comment.objects.create(user=request.user, competition=competition, text=comment_text)
        return redirect('competition_detail', id=id)

    return render(request, 'competition_detail.html', {
        'competition': competition,
        'participants': participants,
        'comments': comments,
        'user_votes': user_votes,
        'user_participation': user_participation,
        'voted_participant_ids': voted_participant_ids,
        'voted_participants': voted_participants,
    })

@login_required
def delete_participant(request, competition_id, participant_id):
    competition = get_object_or_404(Competition, id=competition_id)

    if competition.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете удалить участника.")

    participant = get_object_or_404(Participant, id=participant_id, competition=competition)
    participant.delete()
    return redirect('my_competition_detail', id=competition.id)

def edit_participant(request, competition_id, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    
    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            return redirect('my_competition_detail', id=competition_id)
    else:
        form = ParticipantForm(instance=participant)

    return render(request, 'edit_participant.html', {'form': form, 'competition_id': competition_id})

@login_required
def delete_comment(request, competition_id, comment_id):
    competition = get_object_or_404(Competition, id=competition_id)

    if competition.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Вы не можете удалить комментарии.")

    comment = get_object_or_404(Comment, id=comment_id, competition=competition)
    comment.is_deleted = True
    comment.save()
    return redirect('my_competition_detail', id=competition.id)

@login_required
def my_competitions(request):
    filter_by = request.GET.get('filter', 'all')
    competitions = Competition.objects.filter(owner=request.user)

    for competition in competitions:
        competition.update_status()

    if filter_by == 'available':
        competitions = [c for c in competitions if c.status == 'available']
    elif filter_by == 'voting':
        competitions = [c for c in competitions if c.status == 'voting']
    elif filter_by == 'completed':
        competitions = [c for c in competitions if c.status == 'completed']

    return render(request, 'my_competitions.html', {'competitions': competitions})

@login_required
def my_participant_competitions(request):
    competitions = Competition.objects.filter(participants__user=request.user)

    filter_param = request.GET.get('filter')
    if filter_param:
        if filter_param == 'available':
            competitions = competitions.filter(status='available')
        elif filter_param == 'voting':
            competitions = competitions.filter(status='voting')
        elif filter_param == 'completed':
            competitions = competitions.filter(status='completed')

    return render(request, 'my_participant_competitions.html', {'competitions': competitions})


def competition_results(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)

    participants = (
        Participant.objects.filter(competition=competition)
        .annotate(vote_count=Count('votes'))
        .order_by('-vote_count')
    )

    if participants.exists():
        max_votes = participants[0].vote_count
        winners = [p for p in participants if p.vote_count == max_votes]
        if len(winners) == 1:
            result = f"Победитель: {winners[0].title or 'Без названия'}"
        else:
            result = f"Ничья между: {', '.join([winner.title or 'Без названия' for winner in winners])}"
    else:
        result = "Участников нет"

    return render(request, 'competition_results.html', {
        'competition': competition,
        'participants': participants,
        'result': result,
        'winners': winners if participants.exists() else None,
    })

def delete_competition(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)

    if competition.owner == request.user: 
        if request.method == "POST":
            competition.delete()
            messages.success(request, "Конкурс был успешно удален.")
            return redirect('my_competitions')
    else:
        messages.error(request, "У вас нет прав для удаления этого конкурса.")

    return redirect('my_competitions')