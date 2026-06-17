from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden

from .models import Bid, BidStatus
from .forms import BidSubmitForm
from apps.tenders.models import Tender, TenderStatus
from apps.notifications.models import create_notification, NotificationType

# Role Guard Helpers
def _is_staff(user):
    return user.role in ('admin', 'procurement_officer', 'manager')

@login_required
def bid_list(request):
    """
    Vendor sees only their bids.
    Staff sees all bids across all tenders (or filterable).
    """
    if request.user.is_vendor_user:
        try:
            vendor = request.user.vendor_profile
            bids = Bid.objects.filter(vendor=vendor)
        except Exception:
            messages.error(request, 'You do not have a vendor profile yet.')
            return redirect('vendors:create')
    else:
        bids = Bid.objects.all()

    bids = bids.select_related('tender', 'vendor').order_by('-submitted_at')

    paginator = Paginator(bids, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'bids/list.html', {
        'page_title': 'Bids',
        'bids': page_obj,
        'page_obj': page_obj,
    })

@login_required
def bid_detail(request, pk):
    bid = get_object_or_404(Bid, pk=pk)

    # Vendor can only see their own bid
    if request.user.is_vendor_user:
        try:
            if request.user.vendor_profile.pk != bid.vendor.pk:
                return HttpResponseForbidden()
        except Exception:
            return HttpResponseForbidden()

    return render(request, 'bids/detail.html', {
        'page_title': f'Bid #{bid.pk}',
        'bid': bid,
    })

@login_required
def bid_create(request, tender_pk):
    if not request.user.is_vendor_user:
        messages.error(request, 'Only vendors can submit bids.')
        return redirect('tenders:detail', pk=tender_pk)

    tender = get_object_or_404(Tender, pk=tender_pk)
    
    if tender.status != TenderStatus.OPEN:
        messages.error(request, 'This tender is not open for bidding.')
        return redirect('tenders:detail', pk=tender_pk)

    try:
        vendor = request.user.vendor_profile
        if vendor.status != 'approved':
            messages.error(request, 'Your vendor profile must be approved to submit bids.')
            return redirect('tenders:detail', pk=tender_pk)
    except Exception:
        messages.error(request, 'You do not have a vendor profile.')
        return redirect('vendors:create')

    # Check if already bid
    if Bid.objects.filter(tender=tender, vendor=vendor).exists():
        messages.error(request, 'You have already submitted a bid for this tender.')
        return redirect('tenders:detail', pk=tender_pk)

    if request.method == 'POST':
        form = BidSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.tender = tender
            bid.vendor = vendor
            bid.save()

            # Notify Procurement
            from apps.accounts.models import CustomUser
            procurement_users = CustomUser.objects.filter(role='procurement_officer', is_active=True)
            for po in procurement_users:
                create_notification(
                    recipient=po,
                    notification_type=NotificationType.BID_SUBMITTED,
                    title='New Bid Submitted',
                    message=f'{vendor.company_name} submitted a bid for tender {tender.tender_number}.',
                    action_url=bid.get_absolute_url(),
                    related_bid=bid,
                    related_tender=tender
                )

            messages.success(request, f'Your bid for {tender.tender_number} has been submitted successfully.')
            return redirect('bids:detail', pk=bid.pk)
    else:
        form = BidSubmitForm()

    return render(request, 'bids/create.html', {
        'page_title': 'Submit Bid',
        'form': form,
        'tender': tender,
        'vendor': vendor,
    })

@login_required
def bid_withdraw(request, pk):
    bid = get_object_or_404(Bid, pk=pk)

    if not request.user.is_vendor_user:
        return HttpResponseForbidden()

    try:
        if request.user.vendor_profile.pk != bid.vendor.pk:
            return HttpResponseForbidden()
    except Exception:
        return HttpResponseForbidden()

    if not bid.can_be_withdrawn():
        messages.error(request, 'This bid cannot be withdrawn at this stage.')
        return redirect('bids:detail', pk=bid.pk)

    if request.method == 'POST':
        bid.status = BidStatus.WITHDRAWN
        bid.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Your bid has been withdrawn.')
        return redirect('bids:list')

    return redirect('bids:detail', pk=bid.pk)
