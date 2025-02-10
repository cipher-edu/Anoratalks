from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages # type: ignore
from .forms import *
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.contrib.auth.models import User

def index(request):
    # Barcha foydalanuvchilarni olish
    users = UserProfile.objects.all()

    # Sahifaga ma'lumotlarni uzatish
    return render(request, 'page-modern-agency-about.html', {'users': users})

def register(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            user_profile = form.save(commit=False)

            # Username yaratish
            base_username = f"{user_profile.first_name.lower()}{user_profile.last_name.lower()}"
            user_profile.username = base_username
            num_suffix = 1

            # Noyob username yaratilishini tekshirish
            while UserProfile.objects.filter(username=user_profile.username).exists():
                user_profile.username = f"{base_username}{num_suffix}"
                num_suffix += 1

            try:
                user_profile.save()

                return render(request, 'your_information.html', {
                    'username': user_profile.username,
                    'password': user_profile.password
                })
            except ValidationError as e:
                form.add_error(None, e.message)  # Xatolikni yangi foydalanuvchi formasiga qo'shish
            except IntegrityError:
                form.add_error(None, 'Foydalanuvchi ismi allaqachon mavjud. Iltimos, boshqa bir nom tanlang.')
    else:
        form = UserProfileForm()
    return render(request, 'register.html', {'form': form})
