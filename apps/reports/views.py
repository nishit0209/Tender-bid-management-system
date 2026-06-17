from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
import json

from apps.accounts.models import UserRole
from apps.tenders.models import Tender, TenderStatus
from apps.bids.models import Bid, BidStatus
from apps.purchase_orders.models import PurchaseOrder, POStatus
from apps.vendors.models import Vendor, VendorStatus

@login_required
def reports_index(request):
    """
    Generate System-wide Procurement Insights and Statistics.
    Only accessible to Admins, Managers, and Procurement Officers.
    """
    if request.user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER]:
        return render(request, 'dashboard/index.html')

    # 1. Top Level KPIs
    total_vendors = Vendor.objects.filter(status=VendorStatus.APPROVED).count()
    active_tenders = Tender.objects.filter(status=TenderStatus.OPEN).count()
    awarded_tenders = Tender.objects.filter(status=TenderStatus.AWARDED).count()
    total_bids = Bid.objects.count()

    total_po_value = PurchaseOrder.objects.exclude(status=POStatus.DRAFT).aggregate(total=Sum('total_amount'))['total'] or 0

    # 2. Chart Data: Tenders by Status
    tender_status_counts = Tender.objects.values('status').annotate(count=Count('id'))
    status_labels = []
    status_data = []
    for item in tender_status_counts:
        label = dict(TenderStatus.choices).get(item['status'], item['status'])
        status_labels.append(str(label))
        status_data.append(item['count'])

    # 3. Chart Data: Purchase Order Values by Month (Last 6 Months)
    six_months_ago = timezone.now() - timedelta(days=180)
    recent_pos = PurchaseOrder.objects.filter(created_at__gte=six_months_ago).exclude(status=POStatus.DRAFT)
    
    # Simple manual grouping by month to avoid complex DB specific truncations
    po_by_month = {}
    for po in recent_pos:
        month_str = po.created_at.strftime('%b %Y')
        po_by_month[month_str] = po_by_month.get(month_str, 0) + float(po.total_amount)
        
    po_month_labels = list(po_by_month.keys())
    po_month_data = list(po_by_month.values())

    # 4. Top 5 Vendors by PO Value
    top_vendors = Vendor.objects.annotate(
        po_total=Sum('purchase_orders__total_amount')
    ).order_by('-po_total')[:5]

    context = {
        'total_vendors': total_vendors,
        'active_tenders': active_tenders,
        'awarded_tenders': awarded_tenders,
        'total_bids': total_bids,
        'total_po_value': total_po_value,
        
        # Chart JSONs
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'po_month_labels': json.dumps(po_month_labels),
        'po_month_data': json.dumps(po_month_data),
        
        'top_vendors': top_vendors,
    }

    return render(request, 'reports/index.html', context)
