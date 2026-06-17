from django.db import connection
from allauth.socialaccount.models import SocialApp
import sys
import django
import os

def fix():
    print("Fixing database...")
    with connection.schema_editor() as schema_editor:
        try:
            schema_editor.create_model(SocialApp.sites.through)
            print("Table 'socialaccount_socialapp_sites' created successfully!")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":      
    fix()
