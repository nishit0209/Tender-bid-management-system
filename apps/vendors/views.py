"""
Vendors App — Views
Enterprise Tender & Bid Management System

Workflow:
  Vendor registers → Procurement Officer verifies → Manager approves → Vendor can bid
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseForbidden

from .models import Vendor, VendorDocument, VendorStatus, DocumentStatus
from .forms import (
    VendorRegistrationForm, VendorUpdateForm, DocumentUploadForm,
    VendorRejectForm, VendorSuspendForm, DocumentRejectForm, VendorFilterForm,
)


# ─────────────────────────────────────────────
# Role Guard Helpers
# ─────────────────────────────────────────────
def _is_staff(user):
    return user.role in ('admin', 'procurement_officer', 'manager')

def _is_procurement_or_admin(user):
    return user.role in ('admin', 'procurement_officer')

def _is_manager_or_admin(user):
    return user.role in ('admin', 'manager')


# ─────────────────────────────────────────────
# Vendor List View
# ─────────────────────────────────────────────
@login_required
def vendor_list(request):
    """
    Staff: paginated list of all vendors with search/filter.
    Vendor: redirect to their own profile.
    """
    if request.user.is_vendor_user:
        return redirect('vendors:my_profile')

    if not _is_staff(request.user):
        return HttpResponseForbidden()

    form = VendorFilterForm(request.GET)
    vendors = Vendor.objects.select_related('user').order_by('-created_at')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        status = form.cleaned_data.get('status')
        city = form.cleaned_data.get('city')
        state = form.cleaned_data.get('state')

        if q:
            vendors = vendors.filter(
                Q(company_name__icontains=q) |
                Q(gst_number__icontains=q) |
                Q(pan_number__icontains=q) |
                Q(contact_email__icontains=q) |
                Q(contact_person__icontains=q)
            )
        if status:
            vendors = vendors.filter(status=status)
        if city:
            vendors = vendors.filter(city__icontains=city)
        if state:
            vendors = vendors.filter(state__icontains=state)

    # Stats for header cards
    total      = Vendor.objects.count()
    pending    = Vendor.objects.pending().count()
    verified   = Vendor.objects.verified().count()
    approved   = Vendor.objects.approved().count()

    paginator = Paginator(vendors, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'vendors/list.html', {
        'page_title': 'Vendor Management',
        'filter_form': form,
        'page_obj': page_obj,
        'vendors': page_obj,
        'total': total,
        'pending': pending,
        'verified': verified,
        'approved': approved,
    })


# ─────────────────────────────────────────────
# Vendor Detail View
# ─────────────────────────────────────────────
@login_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)

    # Vendors can only see own profile via my_profile; staff can see all
    if request.user.is_vendor_user:
        try:
            if request.user.vendor_profile.pk != pk:
                return redirect('vendors:my_profile')
        except Exception:
            return redirect('vendors:my_profile')

    documents = vendor.documents.order_by('document_type')
    reject_form  = VendorRejectForm()
    suspend_form = VendorSuspendForm()

    return render(request, 'vendors/detail.html', {
        'page_title': vendor.company_name,
        'vendor': vendor,
        'documents': documents,
        'reject_form': reject_form,
        'suspend_form': suspend_form,
        'can_verify':  _is_procurement_or_admin(request.user) and vendor.status == VendorStatus.PENDING,
        'can_approve': _is_manager_or_admin(request.user) and vendor.status == VendorStatus.VERIFIED,
        'can_reject':  _is_staff(request.user) and vendor.status in (VendorStatus.PENDING, VendorStatus.VERIFIED),
        'can_suspend': _is_manager_or_admin(request.user) and vendor.status == VendorStatus.APPROVED,
    })


# ─────────────────────────────────────────────
# Vendor Create (Self-Registration by Vendor)
# ─────────────────────────────────────────────
@login_required
def vendor_create(request):
    # Admin can create a profile for any user
    # Vendor users can only create their own profile

    if not request.user.is_vendor_user and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to register a vendor profile.')
        return redirect('dashboard:index')

    # Non-admin vendor: check they don't already have a profile
    if request.user.is_vendor_user:
        try:
            existing = request.user.vendor_profile
            messages.info(request, 'You already have a vendor profile.')
            return redirect('vendors:my_profile')
        except Exception:
            pass

    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST)

        # Determine which user gets this vendor profile
        target_user = request.user
        if request.user.role == 'admin':
            from apps.accounts.models import CustomUser
            user_id = request.POST.get('target_user')
            if user_id:
                try:
                    target_user = CustomUser.objects.get(pk=user_id)
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Selected user not found.')
                    return redirect('vendors:create')

        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = target_user
            vendor.status = VendorStatus.PENDING
            vendor.save()

            _notify_procurement_new_vendor(request, vendor)

            messages.success(
                request,
                f'Vendor profile for "{vendor.company_name}" created successfully! '
                'Status: Pending Review.'
            )
            if request.user.role == 'admin':
                return redirect('vendors:detail', pk=vendor.pk)
            return redirect('vendors:my_profile')
    else:
        form = VendorRegistrationForm()

    # For admin: get all users without a vendor profile
    eligible_users = []
    if request.user.role == 'admin':
        from apps.accounts.models import CustomUser
        all_users = CustomUser.objects.filter(is_active=True).order_by('email')
        # Exclude users who already have a vendor profile
        for u in all_users:
            try:
                _ = u.vendor_profile
            except Exception:
                eligible_users.append(u)

    return render(request, 'vendors/create.html', {
        'page_title': 'Register Vendor Profile',
        'form': form,
        'eligible_users': eligible_users,
        'is_admin': request.user.role == 'admin',
    })



# ─────────────────────────────────────────────
# Vendor Update (Edit Own Profile)
# ─────────────────────────────────────────────
@login_required
def vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)

    # Only the vendor themselves or admin can edit
    if request.user.is_vendor_user:
        try:
            if request.user.vendor_profile.pk != pk:
                return HttpResponseForbidden()
        except Exception:
            return HttpResponseForbidden()
    elif request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = VendorUpdateForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor profile updated successfully.')
            return redirect('vendors:detail', pk=vendor.pk)
    else:
        form = VendorUpdateForm(instance=vendor)

    return render(request, 'vendors/edit.html', {
        'page_title': f'Edit — {vendor.company_name}',
        'form': form,
        'vendor': vendor,
    })


# ─────────────────────────────────────────────
# My Profile (Vendor's Own View)
# ─────────────────────────────────────────────
@login_required
def vendor_my_profile(request):
    if not request.user.is_vendor_user:
        return redirect('dashboard:index')

    vendor = None
    documents = []
    try:
        vendor = request.user.vendor_profile
        documents = vendor.documents.order_by('document_type')
    except Exception:
        pass

    return render(request, 'vendors/my_profile.html', {
        'page_title': 'My Vendor Profile',
        'vendor': vendor,
        'documents': documents,
        'has_profile': vendor is not None,
    })


# ─────────────────────────────────────────────
# Vendor Verify (Procurement Officer)
# ─────────────────────────────────────────────
@login_required
def vendor_verify(request, pk):
    if not _is_procurement_or_admin(request.user):
        return HttpResponseForbidden()

    vendor = get_object_or_404(Vendor, pk=pk, status=VendorStatus.PENDING)

    if request.method == 'POST':
        vendor.status = VendorStatus.VERIFIED
        vendor.verified_by = request.user
        vendor.verified_at = timezone.now()
        vendor.save(update_fields=['status', 'verified_by', 'verified_at', 'updated_at'])

        # Notify vendor and manager
        _notify_vendor_verified(request, vendor)

        messages.success(request, f'"{vendor.company_name}" has been verified and sent to Manager for approval.')
        return redirect('vendors:detail', pk=vendor.pk)

    return render(request, 'vendors/confirm_action.html', {
        'page_title': 'Verify Vendor',
        'vendor': vendor,
        'action': 'verify',
        'action_label': 'Verify Vendor',
        'action_color': 'blue',
        'message': f'Are you sure you want to verify "{vendor.company_name}"? This will send the vendor to Manager for final approval.',
    })


# ─────────────────────────────────────────────
# Vendor Approve (Manager)
# ─────────────────────────────────────────────
@login_required
def vendor_approve(request, pk):
    if not _is_manager_or_admin(request.user):
        return HttpResponseForbidden()

    vendor = get_object_or_404(Vendor, pk=pk, status=VendorStatus.VERIFIED)

    if request.method == 'POST':
        vendor.status = VendorStatus.APPROVED
        vendor.approved_by = request.user
        vendor.approved_at = timezone.now()
        vendor.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

        _notify_vendor_approved(request, vendor)

        messages.success(request, f'"{vendor.company_name}" has been approved! The vendor can now submit bids.')
        return redirect('vendors:detail', pk=vendor.pk)

    return render(request, 'vendors/confirm_action.html', {
        'page_title': 'Approve Vendor',
        'vendor': vendor,
        'action': 'approve',
        'action_label': 'Approve Vendor',
        'action_color': 'emerald',
        'message': f'Are you sure you want to approve "{vendor.company_name}"? They will be able to submit bids on open tenders.',
    })


# ─────────────────────────────────────────────
# Vendor Reject
# ─────────────────────────────────────────────
@login_required
def vendor_reject(request, pk):
    if not _is_staff(request.user):
        return HttpResponseForbidden()

    vendor = get_object_or_404(Vendor, pk=pk)
    if vendor.status not in (VendorStatus.PENDING, VendorStatus.VERIFIED):
        messages.error(request, 'This vendor cannot be rejected in its current status.')
        return redirect('vendors:detail', pk=vendor.pk)

    if request.method == 'POST':
        form = VendorRejectForm(request.POST)
        if form.is_valid():
            vendor.status = VendorStatus.REJECTED
            vendor.rejection_reason = form.cleaned_data['reason']
            vendor.save(update_fields=['status', 'rejection_reason', 'updated_at'])

            _notify_vendor_rejected(request, vendor)

            messages.warning(request, f'"{vendor.company_name}" has been rejected.')
            return redirect('vendors:detail', pk=vendor.pk)
    else:
        form = VendorRejectForm()

    return render(request, 'vendors/reject.html', {
        'page_title': 'Reject Vendor',
        'vendor': vendor,
        'form': form,
    })


# ─────────────────────────────────────────────
# Vendor Suspend
# ─────────────────────────────────────────────
@login_required
def vendor_suspend(request, pk):
    if not _is_manager_or_admin(request.user):
        return HttpResponseForbidden()

    vendor = get_object_or_404(Vendor, pk=pk, status=VendorStatus.APPROVED)

    if request.method == 'POST':
        form = VendorSuspendForm(request.POST)
        if form.is_valid():
            vendor.status = VendorStatus.SUSPENDED
            vendor.suspension_reason = form.cleaned_data['reason']
            vendor.save(update_fields=['status', 'suspension_reason', 'updated_at'])
            messages.warning(request, f'"{vendor.company_name}" has been suspended.')
            return redirect('vendors:detail', pk=vendor.pk)
    else:
        form = VendorSuspendForm()

    return render(request, 'vendors/suspend.html', {
        'page_title': 'Suspend Vendor',
        'vendor': vendor,
        'form': form,
    })


# ─────────────────────────────────────────────
# Document Upload (Vendor)
# ─────────────────────────────────────────────
@login_required
def document_upload(request, vendor_pk):
    vendor = get_object_or_404(Vendor, pk=vendor_pk)

    # Only the vendor themselves can upload documents
    if request.user.is_vendor_user:
        try:
            if request.user.vendor_profile.pk != vendor_pk:
                return HttpResponseForbidden()
        except Exception:
            return HttpResponseForbidden()
    elif request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.vendor = vendor
            doc.save()

            # Notify procurement
            _notify_document_uploaded(request, vendor, doc)

            messages.success(request, f'Document "{doc.get_document_type_display()}" uploaded successfully.')
            return redirect('vendors:my_profile')
    else:
        form = DocumentUploadForm()

    return render(request, 'vendors/document_upload.html', {
        'page_title': 'Upload Document',
        'form': form,
        'vendor': vendor,
    })


# ─────────────────────────────────────────────
# Document Verify (Procurement)
# ─────────────────────────────────────────────
@login_required
def document_verify(request, doc_pk):
    if not _is_procurement_or_admin(request.user):
        return HttpResponseForbidden()

    doc = get_object_or_404(VendorDocument, pk=doc_pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'verify':
            doc.status = DocumentStatus.VERIFIED
            doc.verified_by = request.user
            doc.verified_at = timezone.now()
            doc.rejection_reason = ''
            doc.save(update_fields=['status', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])
            messages.success(request, f'Document "{doc.get_document_type_display()}" verified.')
        elif action == 'reject':
            reject_form = DocumentRejectForm(request.POST)
            if reject_form.is_valid():
                doc.status = DocumentStatus.REJECTED
                doc.rejection_reason = reject_form.cleaned_data['reason']
                doc.save(update_fields=['status', 'rejection_reason', 'updated_at'])
                messages.warning(request, f'Document "{doc.get_document_type_display()}" rejected.')
        return redirect('vendors:detail', pk=doc.vendor.pk)

    return redirect('vendors:detail', pk=doc.vendor.pk)


# ─────────────────────────────────────────────
# Document Delete (Vendor — only if pending)
# ─────────────────────────────────────────────
@login_required
def document_delete(request, doc_pk):
    doc = get_object_or_404(VendorDocument, pk=doc_pk)

    if request.user.is_vendor_user:
        try:
            if request.user.vendor_profile.pk != doc.vendor.pk:
                return HttpResponseForbidden()
        except Exception:
            return HttpResponseForbidden()
    elif request.user.role != 'admin':
        return HttpResponseForbidden()

    if doc.status != DocumentStatus.PENDING:
        messages.error(request, 'Only pending documents can be deleted.')
        return redirect('vendors:my_profile')

    if request.method == 'POST':
        doc_name = doc.get_document_type_display()
        doc.delete()
        messages.success(request, f'Document "{doc_name}" deleted.')
        return redirect('vendors:my_profile')

    return render(request, 'vendors/confirm_action.html', {
        'page_title': 'Delete Document',
        'vendor': doc.vendor,
        'action': 'delete',
        'action_label': 'Delete Document',
        'action_color': 'red',
        'message': f'Are you sure you want to delete "{doc.get_document_type_display()}"? This cannot be undone.',
    })


# ─────────────────────────────────────────────
# Notification Helpers (lazy import to avoid circular)
# ─────────────────────────────────────────────
def _notify_procurement_new_vendor(request, vendor):
    try:
        from apps.notifications.models import create_notification, NotificationType
        from apps.accounts.models import CustomUser
        procurement_users = CustomUser.objects.filter(role='procurement_officer', is_active=True)
        for user in procurement_users:
            create_notification(
                recipient=user,
                notification_type=NotificationType.VENDOR_REGISTERED,
                title='New Vendor Registration',
                message=f'{vendor.company_name} has registered and is awaiting your verification.',
                action_url=f'/vendors/{vendor.pk}/',
                related_vendor=vendor,
            )
    except Exception:
        pass


def _notify_vendor_verified(request, vendor):
    try:
        from apps.notifications.models import create_notification, NotificationType
        from apps.accounts.models import CustomUser
        # Notify vendor
        create_notification(
            recipient=vendor.user,
            notification_type=NotificationType.VENDOR_VERIFIED,
            title='Profile Verified',
            message='Your vendor profile has been verified by the Procurement Officer and is now awaiting Manager approval.',
            action_url='/vendors/my-profile/',
            related_vendor=vendor,
        )
        # Notify managers
        managers = CustomUser.objects.filter(role='manager', is_active=True)
        for mgr in managers:
            create_notification(
                recipient=mgr,
                notification_type=NotificationType.VENDOR_VERIFIED,
                title='Vendor Ready for Approval',
                message=f'{vendor.company_name} has been verified and requires your approval.',
                action_url=f'/vendors/{vendor.pk}/',
                related_vendor=vendor,
            )
    except Exception:
        pass


def _notify_vendor_approved(request, vendor):
    try:
        from apps.notifications.models import create_notification, NotificationType
        create_notification(
            recipient=vendor.user,
            notification_type=NotificationType.VENDOR_APPROVED,
            title='Profile Approved!',
            message='Congratulations! Your vendor profile has been approved. You can now browse and submit bids on open tenders.',
            action_url='/tenders/',
            related_vendor=vendor,
        )
    except Exception:
        pass


def _notify_vendor_rejected(request, vendor):
    try:
        from apps.notifications.models import create_notification, NotificationType
        create_notification(
            recipient=vendor.user,
            notification_type=NotificationType.VENDOR_REJECTED,
            title='Profile Rejected',
            message=f'Your vendor profile has been rejected. Reason: {vendor.rejection_reason}',
            action_url='/vendors/my-profile/',
            related_vendor=vendor,
        )
    except Exception:
        pass


def _notify_document_uploaded(request, vendor, doc):
    try:
        from apps.notifications.models import create_notification, NotificationType
        from apps.accounts.models import CustomUser
        procurement_users = CustomUser.objects.filter(role='procurement_officer', is_active=True)
        for user in procurement_users:
            create_notification(
                recipient=user,
                notification_type=NotificationType.DOCUMENT_UPLOADED,
                title='New Document Uploaded',
                message=f'{vendor.company_name} uploaded: {doc.get_document_type_display()}',
                action_url=f'/vendors/{vendor.pk}/',
                related_vendor=vendor,
            )
    except Exception:
        pass
