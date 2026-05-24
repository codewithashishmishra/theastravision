from django.core.management.base import BaseCommand
from core.models import User
import face_recognition
import os

class Command(BaseCommand):
    help = 'Encode face from an image and save it to a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user')
        parser.add_argument('image_path', type=str, help='Absolute path to the image')

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        image_path = kwargs['image_path']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {email} not found."))
            return

        if not os.path.exists(image_path):
            self.stdout.write(self.style.ERROR(f"Image {image_path} not found."))
            return

        try:
            # Load the image
            image = face_recognition.load_image_file(image_path)
            
            # Find all face encodings in the image
            face_encodings = face_recognition.face_encodings(image)
            
            if not face_encodings:
                self.stdout.write(self.style.ERROR("No faces found in the image!"))
                return
                
            if len(face_encodings) > 1:
                self.stdout.write(self.style.WARNING("Multiple faces found! Using the first one."))

            # Save the 128-dimensional encoding as a list (JSON serializable)
            user.face_encoding = face_encodings[0].tolist()
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully encoded face and saved to {email}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to process image: {str(e)}"))
