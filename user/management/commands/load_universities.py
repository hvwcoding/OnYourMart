import json

from django.core.management.base import BaseCommand

from user.models import City, University


class Command(BaseCommand):
    help = 'Load university data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='JSON file containing university data')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        with open(json_file, 'r') as file:
            university_data = json.load(file)

        for entry in university_data:
            city_name = entry['Town']
            university_name = entry['University']

            city, _ = City.objects.get_or_create(name=city_name)
            University.objects.create(name=university_name, city=city)

        self.stdout.write(self.style.SUCCESS('Successfully loaded university data from JSON.'))
