from PIL import Image, ImageOps
from django.core.files import File
from django.core.validators import MinValueValidator
from django.db import models

from user.models import CustomUser, City


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ListingType(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Photo(models.Model):
    listing = models.ForeignKey('Listing', related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='listing_images', null=True, blank=True)
    image_thumbnail = models.ImageField(upload_to='listing_images/thumbnails', null=True, blank=True)

    def resize_image_to_16_9(self, image_field, is_thumbnail=True, output_size=None):
        THUMBNAIL_SIZE = (320, 180)  # for 16:9
        MAIN_IMAGE_SIZE = (1920, 1080)  # for 16:9

        with Image.open(image_field.path) as original:
            width, height = original.size
            target_ratio = 16 / 9
            current_ratio = width / height

            # Image is portrait or square
            if current_ratio <= 1:
                target_width = int(height * target_ratio)
                padding = (target_width - width) // 2
                result = ImageOps.expand(original, (padding, 0, padding, 0), fill='white')

            # Image is landscape
            else:
                # If already 16:9
                if current_ratio == target_ratio:
                    result = original

                # Wider than 16:9
                elif current_ratio > target_ratio:
                    target_height = int(width / target_ratio)
                    padding = (target_height - height) // 2
                    result = ImageOps.expand(original, (0, padding, 0, padding), fill='white')

                # Narrower than 16:9
                else:
                    target_width = int(height * target_ratio)
                    left = (width - target_width) // 2
                    right = left + target_width
                    result = original.crop((left, 0, right, height))

            if not output_size:
                output_size = THUMBNAIL_SIZE if is_thumbnail else MAIN_IMAGE_SIZE

            result = result.resize(output_size, Image.LANCZOS)
            result.save(image_field.path)

    def save(self, *args, **kwargs):
        # Check if the image exists before processing
        if self.image and hasattr(self.image, 'path'):
            # First, save the original image without processing
            super().save(*args, **kwargs)

            # Store the original image path for further processing
            original_image_path = self.image.path

            # Process the main image to 16:9 from the original image
            self.resize_image_to_16_9(self.image, is_thumbnail=False)
            super().save(*args, **kwargs)  # Save the main image after processing

            # Process the thumbnail using the original image
            with open(original_image_path, 'rb') as original_image_file:
                # Attach the original image file to the thumbnail field
                self.image_thumbnail.save(self.image.name, File(original_image_file), save=False)
                self.resize_image_to_16_9(self.image_thumbnail, is_thumbnail=True)
            super().save(*args, **kwargs)  # Save the thumbnail after processing
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.listing.name


class Condition(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class MeetupPoint(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Status(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Listing(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    listing_type = models.ForeignKey(ListingType, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=500)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='listings')
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)], default=0.00)
    meetup_available = models.BooleanField(default=False)
    meetup_point = models.ForeignKey(MeetupPoint, on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, default=1)
    created_date = models.DateTimeField(auto_now_add=True)
