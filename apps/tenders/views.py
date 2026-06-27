from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseForbidden

from .models import Tender, TenderStatus
from .forms import TenderCreateForm, TenderApprovalForm, TenderFilterForm
from apps.bids.models import BidStatus
from apps.notifications.models import create_notification, NotificationType

# Role Guard Helpers
def _is_staff(user):
    return user.role in ('admin', 'procurement_officer', 'manager')

def _is_procurement_or_admin(user):
    return user.role in ('admin', 'procurement_officer')

def _is_manager_or_admin(user):
    return user.role in ('admin', 'manager')

@login_required
def tender_list(request):
    form = TenderFilterForm(request.GET)
    
    # Base queryset depending on role
    if request.user.is_vendor_user:
        # Vendors only see OPEN tenders, or awarded if they participated
        # For now, just show OPEN and active ones
        tenders = Tender.objects.filter(status=TenderStatus.OPEN, is_public=True)
    else:
        # Staff see all tenders
        tenders = Tender.objects.all()

    tenders = tenders.order_by('-created_at')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        status = form.cleaned_data.get('status')
        category = form.cleaned_data.get('category')

        if q:
            tenders = tenders.filter(
                Q(title__icontains=q) |
                Q(tender_number__icontains=q)
            )
        if status:
            tenders = tenders.filter(status=status)
        if category:
            tenders = tenders.filter(category=category)

    # Stats
    total = Tender.objects.count() if not request.user.is_vendor_user else tenders.count()
    open_count = Tender.objects.filter(status=TenderStatus.OPEN).count()
    draft = Tender.objects.filter(status=TenderStatus.DRAFT).count() if not request.user.is_vendor_user else 0
    pending = Tender.objects.filter(status=TenderStatus.PENDING_APPROVAL).count() if not request.user.is_vendor_user else 0

    paginator = Paginator(tenders, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'tenders/list.html', {
        'page_title': 'Tenders',
        'tenders': page_obj,
        'page_obj': page_obj,
        'filter_form': form,
        'total': total,
        'open_count': open_count,
        'draft': draft,
        'pending': pending,
    })

@login_required
def tender_detail(request, pk):
    tender = get_object_or_404(Tender, pk=pk)
    
    # Access check
    if request.user.is_vendor_user and not tender.is_public and tender.status != TenderStatus.OPEN:
        return HttpResponseForbidden("You don't have access to this tender.")

    approval_form = TenderApprovalForm()
    
    winning_bid = None
    l1_bid = None
    if tender.status == TenderStatus.AWARDED:
        winning_bid = tender.bids.filter(status=BidStatus.APPROVED).first()
    
    # Calculate L1 bid (Lowest bidder)
    if tender.bids.exists() and _is_staff(request.user):
        l1_bid = tender.bids.filter(status__in=[BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW, BidStatus.SHORTLISTED]).order_by('bid_amount').first()

    return render(request, 'tenders/detail.html', {
        'page_title': tender.tender_number,
        'tender': tender,
        'approval_form': approval_form,
        'winning_bid': winning_bid,
        'l1_bid': l1_bid,
        'can_edit': _is_procurement_or_admin(request.user) and tender.status == TenderStatus.DRAFT,
        'can_submit': _is_procurement_or_admin(request.user) and tender.status == TenderStatus.DRAFT,
        'can_approve': _is_manager_or_admin(request.user) and tender.status == TenderStatus.PENDING_APPROVAL,
    })

@login_required
def tender_create(request):
    if not _is_procurement_or_admin(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = TenderCreateForm(request.POST, request.FILES)
        if form.is_valid():
            tender = form.save(commit=False)
            tender.created_by = request.user
            tender.status = TenderStatus.DRAFT
            tender.save()
            messages.success(request, f'Tender {tender.tender_number} created successfully as Draft.')
            return redirect('tenders:detail', pk=tender.pk)
    else:
        form = TenderCreateForm()

    return render(request, 'tenders/create.html', {
        'page_title': 'Create Tender',
        'form': form,
    })

@login_required
def tender_edit(request, pk):
    tender = get_object_or_404(Tender, pk=pk)
    
    if not _is_procurement_or_admin(request.user) or tender.status != TenderStatus.DRAFT:
        messages.error(request, 'Only draft tenders can be edited by procurement officers.')
        return redirect('tenders:detail', pk=tender.pk)

    if request.method == 'POST':
        form = TenderCreateForm(request.POST, request.FILES, instance=tender)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tender updated successfully.')
            return redirect('tenders:detail', pk=tender.pk)
    else:
        form = TenderCreateForm(instance=tender)

    return render(request, 'tenders/create.html', {
        'page_title': f'Edit Tender {tender.tender_number}',
        'form': form,
        'is_edit': True,
        'tender': tender,
    })

@login_required
def tender_submit(request, pk):
    if not _is_procurement_or_admin(request.user):
        return HttpResponseForbidden()

    tender = get_object_or_404(Tender, pk=pk, status=TenderStatus.DRAFT)
    
    if request.method == 'POST':
        tender.submit_for_approval(request.user)
        
        # Notify Managers
        from apps.accounts.models import CustomUser
        managers = CustomUser.objects.filter(role='manager', is_active=True)
        for mgr in managers:
            create_notification(
                recipient=mgr,
                notification_type=NotificationType.TENDER_SUBMITTED,
                title='Tender Pending Approval',
                message=f'Tender {tender.tender_number} ({tender.title}) has been submitted for approval.',
                action_url=tender.get_absolute_url(),
                related_tender=tender
            )
            
        messages.success(request, 'Tender submitted for approval.')
        return redirect('tenders:detail', pk=tender.pk)
        
    return redirect('tenders:detail', pk=tender.pk)

@login_required
def tender_approve(request, pk):
    if not _is_manager_or_admin(request.user):
        return HttpResponseForbidden()

    tender = get_object_or_404(Tender, pk=pk, status=TenderStatus.PENDING_APPROVAL)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        tender.approve(request.user, remarks)
        
        create_notification(
            recipient=tender.created_by,
            notification_type=NotificationType.TENDER_APPROVED,
            title='Tender Approved',
            message=f'Your tender {tender.tender_number} has been approved and published.',
            action_url=tender.get_absolute_url(),
            related_tender=tender
        )
        
        from apps.accounts.utils import log_activity
        from apps.accounts.models import SystemLogAction
        log_activity(
            user=request.user,
            action=SystemLogAction.TENDER_PUBLISHED,
            description=f"Approved & published tender {tender.tender_number}",
            request=request
        )
        
        messages.success(request, 'Tender approved and published.')
        return redirect('tenders:detail', pk=tender.pk)

    return redirect('tenders:detail', pk=tender.pk)

@login_required
def tender_reject(request, pk):
    if not _is_manager_or_admin(request.user):
        return HttpResponseForbidden()

    tender = get_object_or_404(Tender, pk=pk, status=TenderStatus.PENDING_APPROVAL)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        if not remarks:
            messages.error(request, 'Remarks are required for rejection.')
            return redirect('tenders:detail', pk=tender.pk)
            
        tender.reject(request.user, remarks)
        
        create_notification(
            recipient=tender.created_by,
            notification_type=NotificationType.TENDER_REJECTED,
            title='Tender Rejected',
            message=f'Your tender {tender.tender_number} was rejected. Reason: {remarks}',
            action_url=tender.get_absolute_url(),
            related_tender=tender
        )
        
        messages.warning(request, 'Tender rejected.')
        return redirect('tenders:detail', pk=tender.pk)

    return redirect('tenders:detail', pk=tender.pk)

@login_required
def tender_close(request, pk):
    if not _is_procurement_or_admin(request.user):
        return HttpResponseForbidden()

    tender = get_object_or_404(Tender, pk=pk, status=TenderStatus.OPEN)
    
    if request.method == 'POST':
        tender.close()
        messages.success(request, 'Tender has been closed for bidding.')
        return redirect('tenders:detail', pk=tender.pk)
        
    return redirect('tenders:detail', pk=tender.pk)

@login_required
def tender_cancel(request, pk):
    if not _is_manager_or_admin(request.user):
        return HttpResponseForbidden()

    tender = get_object_or_404(Tender, pk=pk)
    
    if tender.status in [TenderStatus.CLOSED, TenderStatus.AWARDED, TenderStatus.CANCELLED]:
        messages.error(request, 'This tender cannot be cancelled.')
        return redirect('tenders:detail', pk=tender.pk)
        
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        if not reason:
            messages.error(request, 'Cancellation reason is required.')
            return redirect('tenders:detail', pk=tender.pk)
            
        tender.cancel(reason)
        messages.warning(request, 'Tender has been cancelled.')
        return redirect('tenders:detail', pk=tender.pk)
        
    return redirect('tenders:detail', pk=tender.pk)


@login_required
def tender_export_bids(request, pk):
    import csv
    from django.http import HttpResponse

    if not _is_staff(request.user):
        return HttpResponseForbidden()

    tender = get_object_or_404(Tender, pk=pk)
    bids = tender.bids.all().order_by('bid_amount')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Tender_{tender.tender_number}_Bids.csv"'

    writer = csv.writer(response)
    writer.writerow(['Vendor Name', 'Bid Amount', 'Delivery Days', 'Status', 'Submitted At'])

    for bid in bids:
        writer.writerow([
            bid.vendor.company_name,
            f"{bid.total_bid_amount}",
            f"{bid.delivery_timeline_days} days",
            bid.get_status_display(),
            bid.submitted_at.strftime("%Y-%m-%d %H:%M") if bid.submitted_at else "N/A"
        ])

    return response
