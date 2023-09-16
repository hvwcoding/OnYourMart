from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from listing.models import Category


class Command(BaseCommand):
    help = 'Load categories into the database.'

    def handle(self, *args, **options):
        self.create_categories()

    def create_categories(self):
        categories = {
            'Clothing and Fashion': {
                'Tops': ['T-Shirts', 'Shirts and Blouses', 'Sweaters and Cardigans', 'Hoodies and Sweatshirts',
                         'Jackets and Coats', 'Dresses', 'Skirts', 'Pants and Jeans', 'Activewear', 'Formal Wear',
                         'Other Tops'],
                'Footwear': ['Sneakers', 'Sandals and Flip-Flops', 'Boots and Booties', 'Dress Shoes', 'Athletic Shoes',
                             'Slippers', 'Other Footwear'],
                'Accessories': ['Bags and Backpacks', 'Hats and Caps', 'Scarves and Shawls', 'Belts', 'Sunglasses',
                                'Jewelry and Watches', 'Wallets and Cardholders', 'Other Accessories']
            },
            'Electronics': {
                'Mobile Devices': ['Smartphones', 'Tablets', 'Accessories'],
                'Laptops and Computers': ['Laptops', 'Desktops', 'Monitors', 'Keyboards and Mice', 'Accessories'],
                'Audio': ['Headphones', 'Speakers', 'Earbuds', 'Accessories'],
                'Cameras': ['DSLR Cameras', 'Mirrorless Cameras', 'Point-and-Shoot Cameras', 'Accessories'],
                'Gaming': ['Consoles', 'Games', 'Controllers', 'Accessories']
            },
            'Furniture and Home Essentials': {
                'Furniture': ['Couches and Sofas', 'Chairs', 'Tables', 'Bed Frame', 'Dressers and Wardrobes',
                              'Bookcases', 'Shelves and Storage'],
                'Home Appliances': ['Microwaves', 'Vacuums', 'Irons', 'Fans', 'Air Purifiers', 'Other Home Appliances'],
                'Home Decor': ['Lighting', 'Rugs', 'Curtains', 'Wall Art', 'Mirrors', 'Other Home Decor']
            },
            'Study and Leisure': {
                'Books and Study Materials': ['Textbooks', 'Study Guides', 'Course Notes', 'Other Study Materials',
                                              'stationery'],
                'Sports and Fitness': ['Bicycles', 'Sports Equipment', 'Sports Gear'],
                'Miscellaneous': ['Musical Instruments', 'Board Games', 'Travel Luggage']
            }
        }

        for category_name, subcategories in categories.items():
            try:
                # Check if the category already exists in the database
                category = Category.objects.get(name=category_name)
            except ObjectDoesNotExist:
                # If the category doesn't exist, create it
                category = Category(name=category_name)
                category.save()

            for subcategory_name, sub_subcategories in subcategories.items():
                try:
                    # Check if the subcategory already exists in the database
                    subcategory = Category.objects.get(name=subcategory_name, parent=category)
                except ObjectDoesNotExist:
                    # If the subcategory doesn't exist, create it
                    subcategory = Category(name=subcategory_name, parent=category)
                    subcategory.save()

                for sub_subcategory_name in sub_subcategories:
                    try:
                        # Check if the subsubcategory already exists in the database
                        Category.objects.get(name=sub_subcategory_name, parent=subcategory)
                    except ObjectDoesNotExist:
                        # If the subsubcategory doesn't exist, create it
                        subsubcategory = Category(name=sub_subcategory_name, parent=subcategory)
                        subsubcategory.save()
