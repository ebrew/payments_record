from django import forms
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from django.contrib.auth import get_user_model
from django.forms.widgets import NumberInput
from .models import Organisation, Member

User = get_user_model()


class LoginForm(forms.ModelForm):
    email = forms.EmailField(initial='you@example.com')
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password']


class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=20, required=True)
    middle_name = forms.CharField(max_length=20, required=False, help_text='Optional')
    last_name = forms.CharField(max_length=20, required=True)
    phone_number = PhoneNumberField(required=True, max_length=13, help_text='Include country code')

    class Meta:
        model = User
        fields = ('email', 'first_name', 'middle_name', 'last_name', 'phone_number', 'password1', 'password2')


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'phone_number']

    # def clean_phone_number(self):
    #     return '+233' + self.cleaned_data['phone_number'][-9:]


class ImageProfileForm(forms.Form):
    image = forms.ImageField(label='Upload a 700x700 JPG/PNG image as your profile')


class AddContributionForm(forms.Form):
    name = forms.CharField(max_length=50, min_length=5, required=True, label='Organisation name')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    image = forms.ImageField(required=True, label='Upload a 700x700 JPG/PNG image as a logo')


class UpdateOrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        exclude = ['user', 'type', 'updated_at', 'created_at']


class AddOrganisationalMemberForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=20, required=True)
    middle_name = forms.CharField(max_length=20, required=False, help_text='Optional')
    last_name = forms.CharField(max_length=20, required=True)
    phone_number = PhoneNumberField(required=True, max_length=13, help_text='Include country code')
    # image = forms.ImageField(required=False, label='Optional profile picture')


class AddContributionMemberForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """ Grants access to the request object so that only orgs of the current user
        are given as options"""

        self.request = kwargs.pop('request')
        super(AddContributionMemberForm, self).__init__(*args, **kwargs)
        self.fields['organisation'].queryset = Organisation.objects.filter(
            user=self.request.user)

    class Meta:
        model = Member
        fields = ['organisation', 'email', 'first_name', 'middle_name', 'last_name', 'phone_number', 'image']

    # user = forms.CharField()
    organisation = forms.ModelChoiceField
    email = forms.EmailField(max_length=254, required=True, help_text='For notification purposes')
    first_name = forms.CharField(max_length=20, required=True)
    middle_name = forms.CharField(max_length=20, required=False, help_text='Optional')
    last_name = forms.CharField(max_length=20, required=True)
    phone_number = PhoneNumberField(required=True, max_length=13, help_text='Include country code')
    image = forms.ImageField(required=False, label='Optional profile picture')


class SubdomainForm(forms.Form):
    choices = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Organisation.objects.all()
    )

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop('slug', None)  # Correctly obtains slug from url
        super().__init__(*args, **kwargs)
        self.fields['choices'].queryset = Organisation.objects.filter(user_id=slug)  # you don't need select related


class UpdateMemberForm(forms.ModelForm):
    class Meta:
        model = Member
        exclude = ['user', 'organisation', 'image', 'created_at', 'updated_at']


class MakeContributionalPaymentsForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Member.objects.all())
    # member = forms.ModelChoiceField(queryset=Member.objects.filter(organisation_id=5))
    amount = forms.DecimalField(max_digits=6, min_value=1, decimal_places=2)


class DirectContributionalPaymentsForm(forms.Form):
    amount = forms.DecimalField(max_digits=6, min_value=1, decimal_places=2)
