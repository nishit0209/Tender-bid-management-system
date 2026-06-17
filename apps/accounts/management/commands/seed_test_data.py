"""
Management Command: seed_test_data
Creates test users (Procurement Officer, Manager, Vendors) and sample vendor profiles.
Usage: python manage.py seed_test_data
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser, UserRole
from apps.vendors.models import Vendor, VendorStatus


class Command(BaseCommand):
    help = 'Create test users and sample vendor data for development'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== Seeding Test Data ===\n'))

        # ─────────────────────────────────────────
        # 1. Create Users
        # ─────────────────────────────────────────
        users_data = [
            {
                'email': 'procurement@tenderbms.com',
                'first_name': 'Rajesh',
                'last_name': 'Kumar',
                'role': UserRole.PROCUREMENT_OFFICER,
                'phone': '9898123456',
                'department': 'Procurement',
                'designation': 'Senior Procurement Officer',
            },
            {
                'email': 'manager@tenderbms.com',
                'first_name': 'Suresh',
                'last_name': 'Sharma',
                'role': UserRole.MANAGER,
                'phone': '9876500001',
                'department': 'Management',
                'designation': 'General Manager',
            },
            {
                'email': 'vendor1@tenderbms.com',
                'first_name': 'Amit',
                'last_name': 'Patel',
                'role': UserRole.VENDOR,
                'phone': '9876543210',
            },
            {
                'email': 'vendor2@tenderbms.com',
                'first_name': 'Priya',
                'last_name': 'Shah',
                'role': UserRole.VENDOR,
                'phone': '9123456789',
            },
            {
                'email': 'vendor3@tenderbms.com',
                'first_name': 'Kiran',
                'last_name': 'Desai',
                'role': UserRole.VENDOR,
                'phone': '9988776655',
            },
        ]

        created_users = {}
        for data in users_data:
            email = data['email']
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    **data,
                    'is_verified': True,
                }
            )
            if created:
                user.set_password('Test@1234')
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ Created: {email:35} | {user.get_role_display()}'
                ))
            else:
                self.stdout.write(f'  ⏭️  Exists:  {email:35} | {user.get_role_display()}')
            created_users[email] = user

        # ─────────────────────────────────────────
        # 2. Create Vendor Profiles
        # ─────────────────────────────────────────
        self.stdout.write(self.style.WARNING('\n--- Vendor Profiles ---'))

        vendors_data = [
            {
                'user_email': 'vendor1@tenderbms.com',
                'company_name': 'TechnoSoft Solutions Pvt. Ltd.',
                'gst_number': '24AABCT1234R1ZX',
                'pan_number': 'AABCT1234R',
                'cin_number': 'U72200GJ2015PTC084523',
                'contact_person': 'Amit Patel',
                'contact_email': 'amit@technosoft.in',
                'contact_phone': '9876543210',
                'website': 'https://www.technosoft.in',
                'address_line1': '401, TechPark Tower, SG Highway',
                'city': 'Ahmedabad',
                'state': 'Gujarat',
                'pincode': '380015',
                'business_type': 'IT Services & Software Development',
                'year_established': 2015,
                'annual_turnover': 25000000.00,
                'employee_count': 120,
                'category_of_goods': 'Software Development, Cloud Services, ERP Solutions, IT Consulting',
                'bank_name': 'HDFC Bank',
                'bank_account_number': '50100123456789',
                'bank_ifsc': 'HDFC0001234',
                'bank_branch': 'SG Highway, Ahmedabad',
                'status': VendorStatus.PENDING,
            },
            {
                'user_email': 'vendor2@tenderbms.com',
                'company_name': 'Gujarat Office Supplies Co.',
                'gst_number': '24AABCG5678S1ZY',
                'pan_number': 'AABCG5678S',
                'contact_person': 'Priya Shah',
                'contact_email': 'priya@gujoffice.com',
                'contact_phone': '9123456789',
                'address_line1': '12, Industrial Estate, Phase 2',
                'address_line2': 'Near GIDC, Vatva',
                'city': 'Ahmedabad',
                'state': 'Gujarat',
                'pincode': '382445',
                'business_type': 'Manufacturer & Trader',
                'year_established': 2008,
                'annual_turnover': 80000000.00,
                'employee_count': 250,
                'category_of_goods': 'Office Furniture, Stationery, Printers, Computer Peripherals',
                'bank_name': 'State Bank of India',
                'bank_account_number': '38912345678',
                'bank_ifsc': 'SBIN0005432',
                'bank_branch': 'Vatva Industrial, Ahmedabad',
                'status': VendorStatus.PENDING,
            },
            {
                'user_email': 'vendor3@tenderbms.com',
                'company_name': 'BuildRight Infrastructure Ltd.',
                'gst_number': '27AABCB9012L1ZW',
                'pan_number': 'AABCB9012L',
                'msme_number': 'UDYAM-GJ-01-0012345',
                'contact_person': 'Kiran Desai',
                'contact_email': 'kiran@buildright.co.in',
                'contact_phone': '9988776655',
                'alternate_phone': '9988776600',
                'website': 'https://www.buildright.co.in',
                'address_line1': '88, Builder House, Ring Road',
                'city': 'Rajkot',
                'state': 'Gujarat',
                'pincode': '360001',
                'business_type': 'Civil Construction & Infrastructure',
                'year_established': 2003,
                'annual_turnover': 150000000.00,
                'employee_count': 500,
                'category_of_goods': 'Civil Construction, Road Building, Building Materials, Heavy Equipment',
                'bank_name': 'Bank of Baroda',
                'bank_account_number': '21340123456789',
                'bank_ifsc': 'BARB0RAJKOT',
                'bank_branch': 'Ring Road, Rajkot',
                'status': VendorStatus.PENDING,
            },
        ]

        # Also try to create for existing vishal user
        try:
            vishal = CustomUser.objects.get(email__icontains='vishal')
            vendors_data.insert(0, {
                'user_email': vishal.email,
                'company_name': 'Vishal Enterprises Pvt. Ltd.',
                'gst_number': '24AABCV7777R1ZQ',
                'pan_number': 'AABCV7777R',
                'contact_person': 'Vishal Patel',
                'contact_email': vishal.email,
                'contact_phone': '9876543210',
                'address_line1': '55, Commerce House, CG Road',
                'city': 'Ahmedabad',
                'state': 'Gujarat',
                'pincode': '380009',
                'business_type': 'General Trading',
                'year_established': 2018,
                'annual_turnover': 10000000.00,
                'employee_count': 30,
                'category_of_goods': 'General Supplies, Electronics, Hardware',
                'bank_name': 'ICICI Bank',
                'bank_account_number': '123456789012',
                'bank_ifsc': 'ICIC0001234',
                'bank_branch': 'CG Road, Ahmedabad',
                'status': VendorStatus.PENDING,
            })
        except CustomUser.DoesNotExist:
            pass

        for vdata in vendors_data:
            user_email = vdata.pop('user_email')
            try:
                user = CustomUser.objects.get(email=user_email)
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ❌ User not found: {user_email}'))
                continue

            # Check if vendor already exists
            try:
                existing = user.vendor_profile
                self.stdout.write(f'  ⏭️  Vendor exists: {existing.company_name}')
                continue
            except Exception:
                pass

            vendor = Vendor.objects.create(user=user, **vdata)
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ Vendor: {vendor.company_name:35} | {vendor.city:15} | {vendor.get_status_display()}'
            ))

        # ─────────────────────────────────────────
        # Summary
        # ─────────────────────────────────────────
        self.stdout.write(self.style.WARNING('\n=== Login Credentials ==='))
        self.stdout.write('')
        self.stdout.write(f'  {"EMAIL":35} {"PASSWORD":15} {"ROLE"}')
        self.stdout.write(f'  {"─"*35} {"─"*15} {"─"*25}')
        self.stdout.write(f'  {"admin@gmail.com":35} {"(your password)":15} {"Administrator"}')
        self.stdout.write(f'  {"procurement@tenderbms.com":35} {"Test@1234":15} {"Procurement Officer"}')
        self.stdout.write(f'  {"manager@tenderbms.com":35} {"Test@1234":15} {"Manager"}')
        self.stdout.write(f'  {"vendor1@tenderbms.com":35} {"Test@1234":15} {"Vendor"}')
        self.stdout.write(f'  {"vendor2@tenderbms.com":35} {"Test@1234":15} {"Vendor"}')
        self.stdout.write(f'  {"vendor3@tenderbms.com":35} {"Test@1234":15} {"Vendor"}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Test Data Seeded Successfully! ===\n'))
