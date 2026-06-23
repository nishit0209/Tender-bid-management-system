from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from apps.accounts.models import UserRole, CustomUser
from apps.bids.models import Bid, BidStatus
from apps.evaluations.models import Evaluation, EvaluationStatus
from apps.notifications.models import create_notification, NotificationType
from .models import PurchaseOrder, POStatus
from .forms import POCreateForm, PODeliveryForm

@login_required
def po_list(request):
    """List Purchase Orders based on role."""
    if request.user.role == UserRole.VENDOR:
        # Get vendor instance linked to this user
        vendor = getattr(request.user, 'vendor_profile', None)
        if vendor:
            pos = PurchaseOrder.objects.for_vendor(vendor).exclude(status=POStatus.DRAFT)
        else:
            pos = []
    else:
        # Staff sees all POs
        pos = PurchaseOrder.objects.all()

    return render(request, 'purchase_orders/list.html', {
        'pos': pos,
        'page_title': 'Purchase Orders'
    })

@login_required
def po_detail(request, pk):
    """View details of a specific PO."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    # Access control
    if request.user.role == UserRole.VENDOR:
        vendor = getattr(request.user, 'vendor_profile', None)
        if not vendor or po.vendor != vendor:
            messages.error(request, 'Access denied.')
            return redirect('dashboard:index')

    delivery_form = PODeliveryForm(instance=po) if request.user.role == UserRole.VENDOR else None

    return render(request, 'purchase_orders/detail.html', {
        'po': po,
        'delivery_form': delivery_form,
        'page_title': f'{po.po_number}'
    })

@login_required
def po_generate(request, bid_id):
    """Procurement drafts a PO from a winning bid."""
    if request.user.role not in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER]:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    bid = get_object_or_404(Bid, pk=bid_id, status=BidStatus.APPROVED)
    
    # Check if PO already exists
    if hasattr(bid.evaluation, 'purchase_order') and bid.evaluation.purchase_order is not None:
        messages.info(request, 'Purchase Order already exists for this bid.')
        return redirect('purchase_orders:detail', pk=bid.evaluation.purchase_order.pk)

    if request.method == 'POST':
        form = POCreateForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.tender = bid.tender
            po.vendor = bid.vendor
            po.evaluation = bid.evaluation
            po.amount = bid.total_bid_amount
            po.generated_by = request.user
            po.status = POStatus.PENDING # Send to manager
            
            # Simple line items mapping from bid if any
            po.line_items = [
                {
                    'name': bid.tender.title, 
                    'qty': float(bid.tender.quantity) if bid.tender.quantity else 0.0, 
                    'unit': bid.tender.unit, 
                    'rate': float(bid.total_bid_amount), 
                    'amount': float(bid.total_bid_amount)
                }
            ]
            
            po.save()
            
            # Notify Managers
            managers = CustomUser.objects.filter(role=UserRole.MANAGER, is_active=True)
            for manager in managers:
                create_notification(
                    recipient=manager,
                    notification_type=NotificationType.PO_GENERATED,
                    title=f"New Purchase Order Draft: {po.po_number}",
                    message=f"Procurement Officer {request.user.full_name} has drafted a PO for tender '{bid.tender.tender_number}'. Needs your approval.",
                    action_url=po.get_absolute_url(),
                    related_po=po
                )
            
            messages.success(request, 'Purchase Order drafted and sent for Manager Approval.')
            return redirect('purchase_orders:detail', pk=po.pk)
    else:
        # Pre-fill some defaults
        form = POCreateForm(initial={
            'terms_and_conditions': bid.tender.terms_and_conditions or 'Standard terms apply.',
            'delivery_address': 'Central Warehouse, Procurement Dept.',
            'delivery_date': timezone.now().date() + timezone.timedelta(days=bid.delivery_timeline_days)
        })

    return render(request, 'purchase_orders/form.html', {
        'form': form,
        'bid': bid,
        'page_title': 'Generate Purchase Order'
    })

@login_required
def po_action(request, pk, action):
    """Handle PO state transitions."""
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method != 'POST':
        return redirect('purchase_orders:detail', pk=pk)

    # Manager Approve
    if action == 'approve' and request.user.role in [UserRole.ADMIN, UserRole.MANAGER]:
        po.status = POStatus.APPROVED
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()
        
        # Notify Vendor
        create_notification(
            recipient=po.vendor.user,
            notification_type=NotificationType.PO_APPROVED,
            title=f"Purchase Order Approved: {po.po_number}",
            message=f"Your Purchase Order for tender '{po.tender.tender_number}' has been approved. Please prepare for dispatch.",
            action_url=po.get_absolute_url(),
            related_po=po
        )
        
        # Send Email if checked
        if request.POST.get('send_email') == 'on':
            try:
                html_content = render_to_string('emails/po_receipt.html', {'po': po})
                send_mail(
                    subject=f"Purchase Order {po.po_number} Approved - {po.tender.title}",
                    message=f"Your Purchase Order {po.po_number} has been approved. Please view the HTML version for details.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[po.vendor.user.email],
                    fail_silently=True,
                    html_message=html_content
                )
                messages.success(request, 'Purchase Order Approved. Vendor has been notified and email sent.')
            except Exception as e:
                messages.warning(request, 'Purchase Order Approved, but email failed to send.')
        else:
            messages.success(request, 'Purchase Order Approved. Vendor has been notified in-app.')

    # Vendor Dispatch
    elif action == 'dispatch' and request.user.role == UserRole.VENDOR:
        po.status = POStatus.IN_PROGRESS
        po.dispatched_at = timezone.now()
        po.save()
        
        # Notify Procurement and Manager
        staff_users = CustomUser.objects.filter(role__in=[UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER], is_active=True)
        for staff in staff_users:
            create_notification(
                recipient=staff,
                notification_type=NotificationType.PO_DISPATCHED,
                title=f"PO Dispatched: {po.po_number}",
                message=f"{po.vendor.company_name} has marked PO {po.po_number} as dispatched.",
                action_url=po.get_absolute_url(),
                related_po=po
            )
            
        messages.success(request, 'Purchase Order marked as Dispatched.')

    # Vendor Deliver
    elif action == 'deliver' and request.user.role == UserRole.VENDOR:
        form = PODeliveryForm(request.POST, request.FILES, instance=po)
        if form.is_valid():
            po = form.save(commit=False)
            po.status = POStatus.DELIVERED
            po.delivered_at = timezone.now()
            po.save()
            
            # Notify Procurement and Manager
            staff_users = CustomUser.objects.filter(role__in=[UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER], is_active=True)
            for staff in staff_users:
                create_notification(
                    recipient=staff,
                    notification_type=NotificationType.PO_DELIVERED,
                    title=f"PO Delivered: {po.po_number}",
                    message=f"{po.vendor.company_name} has marked PO {po.po_number} as delivered and uploaded proof. Awaiting payment/completion.",
                    action_url=po.get_absolute_url(),
                    related_po=po
                )
                
            messages.success(request, 'Delivery Proof uploaded. PO marked as Delivered.')
        else:
            messages.error(request, 'Failed to upload delivery proof.')

    # Complete PO
    elif action == 'complete' and request.user.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER]:
        po.status = POStatus.COMPLETED
        po.save()
        messages.success(request, 'Purchase Order marked as Completed.')
        
    # Send Email manually
    elif action == 'send_email' and request.user.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER]:
        try:
            html_content = render_to_string('emails/po_receipt.html', {'po': po})
            send_mail(
                subject=f"Purchase Order {po.po_number} - {po.tender.title}",
                message=f"Please view the HTML version for your Purchase Order {po.po_number} details.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[po.vendor.user.email],
                fail_silently=False,
                html_message=html_content
            )
            messages.success(request, f'Email receipt sent to {po.vendor.user.email}')
        except Exception as e:
            messages.error(request, f'Failed to send email. Check your SMTP settings in .env file. Error: {str(e)}')

    else:
        messages.error(request, 'Invalid action or access denied.')

    return redirect('purchase_orders:detail', pk=pk)
