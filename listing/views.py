from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, AccessMixin
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View

from order.models import Order
from user.models import City
from .forms import ListingForm
from .models import Photo, Listing


class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        listings = Listing.objects.filter(status=1)
        return render(request, self.template_name, {'listings': listings})


class ListingMixin:
    template_name = ''
    form_class = ListingForm

    def get_listing(self, pk=None):
        if pk:
            return get_object_or_404(Listing, pk=pk)
        return None

    def get_photo_formset_class(self):
        return inlineformset_factory(Listing, Photo, fields=('image',), extra=6, max_num=6)

    def get_form_and_formset(self, request, listing=None):
        form = self.form_class(request.POST or None, request.FILES or None, instance=listing)
        formset = self.get_photo_formset_class()(request.POST or None, request.FILES or None, instance=listing)
        return form, formset

    def get_common_context(self, request, listing=None):
        form, formset = self.get_form_and_formset(request, listing)
        context = {'form': form, 'formset': formset, 'listing': listing, 'is_update': listing is not None}
        return context

    def render_template(self, request, context, template_name=None):
        template_name = template_name or self.template_name
        return render(request, template_name, context)

    def save_listing(self, request, form, formset):
        listing_obj = form.save(commit=False)
        listing_obj.user = request.user
        listing_obj.category = form.cleaned_data.get('category')
        listing_obj.save()
        formset.instance = listing_obj
        formset.save()
        return redirect('listing_details', pk=listing_obj.pk)


class ListingCreateOrUpdateView(LoginRequiredMixin, UserPassesTestMixin, ListingMixin, View):
    template_name = 'create_or_update_listing.html'

    def test_func(self):
        if 'pk' in self.kwargs:  # Update mode
            listing = self.get_listing(self.kwargs['pk'])
            return self.request.user == listing.user
        return True  # Create mode

    def get(self, request, *args, **kwargs):
        context = self.get_common_context(request, listing=self.get_listing(kwargs.get('pk')))
        return self.render_template(request, context)

    def post(self, request, *args, **kwargs):
        listing = self.get_listing(kwargs.get('pk'))
        form, formset = self.get_form_and_formset(request, listing)

        # Checking cleared image
        images_cleared = any(
            'image-clear' in form.prefix and form.cleaned_data.get('image-clear')
            for form in formset
        )

        # Main processing
        if form.is_valid() and formset.is_valid():
            if 'pk' in kwargs:  # Update mode
                if form.has_changed() or formset.has_changed() or images_cleared:
                    if form.has_changed():
                        form.save()
                    formset.save()  # Save formset regardless of whether main form has changes
                    messages.success(request, 'Your listing has been updated!')
                    return redirect('listing_details', pk=kwargs['pk'])
                else:
                    messages.warning(request, 'No changes detected. Nothing to update.')
            else:  # Create mode
                messages.success(request, 'Your listing has been created!')
                return self.save_listing(request, form, formset)
        context = self.get_common_context(request, listing)
        return self.render_template(request, context)


class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, ListingMixin, View):

    def test_func(self):
        listing = self.get_listing(self.kwargs['pk'])
        return self.request.user == listing.user

    def handle_no_permission(self):
        return HttpResponseForbidden()

    def post(self, request, pk):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponseForbidden()

        listing = self.get_listing(pk)
        listing.delete()
        messages.success(request, 'Your listing has been deleted successfully!')
        redirect_url = reverse('kpi_user')
        return JsonResponse({'status': 'success', 'redirect_url': redirect_url}, status=200)


class ListingSearchView(View):
    template_name = 'search_listing.html'

    def get_filtered_queryset(self, params):
        queryset = Listing.objects.filter(status=1)

        # filter logic
        type_filter = params.get('type')
        city_filter = params.get('city')
        condition_filter = params.get('condition')
        meetup_filter = params.get('meetup')
        query = params.get('query')

        if type_filter:
            queryset = queryset.filter(listing_type__name=type_filter)
        if city_filter:
            queryset = queryset.filter(user__city=city_filter)
        if condition_filter:
            queryset = queryset.filter(condition__name=condition_filter)
        if meetup_filter:
            queryset = queryset.filter(meetup_available=(meetup_filter == "1"))
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))

        # sorting logic
        sort_option = params.get('sort', 'move_out_date')
        if sort_option == 'recently_added':
            queryset = queryset.order_by('-created_date')
        elif sort_option == 'price_low_to_high':
            queryset = queryset.order_by('price')
        elif sort_option == 'price_high_to_low':
            queryset = queryset.order_by('-price')
        # elif sort_option == 'move_out_date':
        #     queryset = queryset.order_by('user__move_out_date')

        return queryset

    def get(self, request):
        listings = self.get_filtered_queryset(request.GET)
        no_results = False

        if not listings.exists():
            no_results = True

        context = {
            'listings': listings,
            'cities': City.objects.all(),
            'no_results': no_results,
            'sort_options': [
                {'value': 'recently_added', 'label': 'Recently Added'},
                {'value': 'price_low_to_high', 'label': 'Price: Low to High'},
                {'value': 'price_high_to_low', 'label': 'Price: High to Low'},
                # {'value': 'move_out_date', 'label': 'Soonest Move Out Date'}
            ]
        }
        return render(request, self.template_name, context)


class ListingDetailsView(AccessMixin, ListingMixin, View):
    template_name = 'listing_details.html'

    def get_context_for_user(self, request, listing):
        context = {'owner': request.user == listing.user}
        context['authenticated'] = request.user.is_authenticated and not context['owner']

        try:
            order = Order.objects.get(listing=listing)
            context['order'] = order
            context['buyer'] = request.user == order.buyer
            context['seller'] = request.user == order.seller
        except Order.DoesNotExist:
            pass

        if not request.user.is_authenticated:
            context['login_url'] = reverse('login')

        return context

    def get(self, request, pk):
        listing = self.get_listing(pk)
        context = self.get_common_context(request, listing)
        user_context = self.get_context_for_user(request, listing)
        context.update(user_context)

        return self.render_template(request, context)
