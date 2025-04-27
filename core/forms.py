# --- START OF FILE forms.py (To'liq va Tuzatilgan) ---

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model # User modelini olish uchun

# Modellarni import qilish (agar Test ga havola kerak bo'lsa)
# To'g'ri import yo'lini ko'rsating
from core.models import Question, Answer, Test # Kerakli modellar

# User modelini olish
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text=_("Iltimos, haqiqiy email manzilingizni kiriting."),
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label=_("Ism")
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label=_("Familiya")
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    # TUZATILDI: clean_email metodi to'g'ri formatlandi
    def clean_email(self):
        """
        Email manzili allaqachon tizimda mavjud emasligini tekshiradi.
        """
        email = self.cleaned_data.get('email')
        if email: # Email kiritilganligini tekshirish
            # O'zgartirish emas, yangi foydalanuvchi yaratish holatini tekshirish
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(_("Bu email manzili allaqachon ro'yxatdan o'tgan."))
        return email


class CustomAuthenticationForm(AuthenticationForm):
    """Login uchun standart forma (moslashtirilgan placeholderlar bilan)"""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': _('Foydalanuvchi nomi'), 'class': 'form-control'})
    )
    password = forms.CharField(
        label=_("Parol"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': _('Parol'), 'class': 'form-control'}),
    )


class TestSubmissionForm(forms.Form):
    """
    Test javoblarini qabul qilish uchun dinamik yaratiladigan forma.
    Har bir savol uchun RadioSelect widget ishlatiladi.
    """
    def __init__(self, *args, **kwargs):
        test_instance = kwargs.pop('test', None)
        if not isinstance(test_instance, Test):
             raise ValueError("TestSubmissionForm 'test' argumentini talab qiladi.")

        super().__init__(*args, **kwargs)
        self.test = test_instance

        questions = self.test.questions.prefetch_related('answers').order_by('order')

        for question in questions:
            choices = [(answer.pk, answer.text) for answer in question.answers.all()]
            if not choices: continue # Javobsiz savollarni o'tkazamiz

            field_name = f'question_{question.pk}'
            self.fields[field_name] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                required=True,
                error_messages={'required': _("Iltimos, ushbu savolga javob tanlang.")}
            )

    # TUZATILDI: get_user_answers metodi to'g'ri formatlandi
    def get_user_answers(self) -> dict:
        """
        Forma validatsiyadan o'tgandan so'ng, foydalanuvchi javoblarini
        {'question_pk': 'answer_pk', ...} formatida qaytaradi.
        """
        answers = {}
        if self.is_valid():
            for name, value in self.cleaned_data.items():
                if name.startswith('question_'):
                    question_pk_str = name.split('_')[1]
                    answers[question_pk_str] = value
        return answers

# --- END OF FILE forms.py ---