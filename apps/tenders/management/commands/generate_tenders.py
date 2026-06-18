import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.tenders.models import Tender, TenderCategory, TenderType, TenderStatus
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate dummy tender data with documents'

    def handle(self, *args, **kwargs):
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create one first or run this locally.'))
            return

        titles = [
            'Supply of High-Performance IT Equipment (Laptops & Desktops)',
            'Construction of New Office Wing Block B',
            'Annual Comprehensive Maintenance Contract for HVAC Systems',
            'Procurement of Eco-Friendly Office Stationery',
            'Consulting Services for Enterprise Digital Transformation',
        ]
        categories = [TenderCategory.IT, TenderCategory.WORKS, TenderCategory.MAINTENANCE, TenderCategory.GOODS, TenderCategory.CONSULTING]
        budgets = [1500000.00, 50000000.00, 500000.00, 100000.00, 2500000.00]
        quantities = [50, 1, 1, 1000, 1]
        units = ['Nos', 'Project', 'Year', 'Packets', 'Project']

        # Dummy PDF file content representing a valid blank PDF
        dummy_pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 53 >>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Dummy Tender Document) Tj\nET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000222 00000 n \n0000000326 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n386\n%%EOF'

        now = timezone.now()

        created_count = 0
        for i in range(5):
            # Check if title already exists to avoid duplicates if run multiple times
            if Tender.objects.filter(title=titles[i]).exists():
                self.stdout.write(self.style.WARNING(f'Tender already exists: {titles[i]}'))
                continue

            tnd = Tender(
                title=titles[i],
                description=f"Detailed description for {titles[i]}. This tender covers all requirements specified by the procurement department. Vendors are expected to meet the technical and financial criteria.",
                category=categories[i],
                tender_type=TenderType.OPEN,
                quantity=quantities[i],
                unit=units[i],
                specifications="1. Must meet ISO 9001 standards.\n2. Warranty of at least 1 year.\n3. Complete documentation required.",
                estimated_budget=budgets[i],
                emd_amount=budgets[i] * 0.02, # 2% EMD
                opening_date=now - timedelta(days=2),
                closing_date=now + timedelta(days=random.randint(5, 30)),
                evaluation_date=now + timedelta(days=35),
                delivery_deadline=(now + timedelta(days=90)).date(),
                terms_and_conditions="1. Delivery must be within the stipulated time.\n2. Payment within 30 days of delivery.\n3. The organization reserves the right to cancel the tender at any time.",
                status=TenderStatus.OPEN,
                created_by=admin_user,
                approved_by=admin_user,
                approved_at=now - timedelta(days=3),
                publish_date=now - timedelta(days=2),
                is_public=True
            )
            
            # Use SimpleUploadedFile to attach a dummy PDF
            pdf_name = f"tender_document_{i+1}.pdf"
            dummy_file = SimpleUploadedFile(pdf_name, dummy_pdf_content, content_type='application/pdf')
            tnd.tender_document = dummy_file
            
            tnd.save()
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully created Tender: {tnd.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal {created_count} tenders created with PDF documents.'))
