from django import forms
from django.forms import inlineformset_factory

from .models import Listing, Category, Condition, ListingType, Photo


def get_all_categories():
    return list(Category.objects.all())


def get_hierarchical_choices(categories, parent=None, level=0):
    current_level_categories = [cat for cat in categories if cat.parent == parent]

    choices = []
    for category in current_level_categories:
        choices.append((category.id, '-' * level + category.name))
        choices += get_hierarchical_choices(categories, category, level + 1)

    return choices


class CustomSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        level = label.count('-')
        actual_label = label
        option_dict = super().create_option(name, value, actual_label, selected, index, subindex=subindex, attrs=attrs)
        option_dict['attrs']['class'] = 'level-{}'.format(level)

        if level < 2:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict


class ListingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)
        self.fields['category'].choices = [('', '---------')] + get_hierarchical_choices(get_all_categories())

    listing_type = forms.ModelChoiceField(
        queryset=ListingType.objects.all(),
        required=True)
    name = forms.CharField(
        label='Title',
        required=True,
        help_text='Max length: 30 characters')
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 5, 'cols': 50}),
        help_text='Max length: 500 characters')
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        widget=CustomSelect()
    )
    condition = forms.ModelChoiceField(
        queryset=Condition.objects.all(),
        required=True)
    price = forms.DecimalField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '£0.00'}))

    class Meta:
        model = Listing
        fields = [
            'listing_type', 'name', 'description', 'category', 'condition',
            'price', 'meetup_available', 'meetup_point',
        ]

    def clean(self):
        cleaned_data = super(ListingForm, self).clean()
        meetup_available = cleaned_data.get('meetup_available')
        meetup_point = cleaned_data.get('meetup_point')
        if meetup_available and not meetup_point:
            self.add_error('meetup_point', 'Please select a meetup point.')
        return cleaned_data

    def save(self, commit=True):
        listing = super(ListingForm, self).save(commit=False)
        listing.listing_type = self.cleaned_data['listing_type']
        listing.name = self.cleaned_data['name']
        listing.description = self.cleaned_data['description']
        listing.category = self.cleaned_data['category']
        listing.condition = self.cleaned_data['condition']
        listing.price = self.cleaned_data['price']

        # If meetup_available is False, set meetup_point to None
        if not self.cleaned_data['meetup_available']:
            listing.meetup_point = None
        else:
            listing.meetup_point = self.cleaned_data['meetup_point']

        if commit:
            listing.save()
        return listing


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ('image',)


PhotoFormSet = inlineformset_factory(
    Listing, Photo,
    form=PhotoForm,
    extra=6,
    max_num=6,
    can_delete=True
)
