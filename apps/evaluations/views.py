from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from apps.accounts.models import UserRole
from apps.tenders.models import Tender, TenderStatus
from apps.bids.models import Bid, BidStatus
from .models import Evaluation, EvaluationStatus
from .forms import EvaluationForm

@login_required
def evaluation_list(request):
    """Generic list of tenders that require evaluation or approval."""
    if request.user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER]:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    tenders = Tender.objects.filter(
        Q(status=TenderStatus.CLOSED) | 
        Q(status=TenderStatus.UNDER_EVALUATION) |
        Q(status=TenderStatus.PENDING_APPROVAL)
    ).order_by('-updated_at')

    return render(request, 'evaluations/tenders_list.html', {
        'tenders': tenders,
        'page_title': 'Tenders Pending Evaluation'
    })

@login_required
def tender_evaluation_list(request, tender_id):
    """Shows the leaderboard/evaluations for a specific tender."""
    tender = get_object_or_404(Tender, id=tender_id)
    
    # Must be manager or procurement or admin
    if request.user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER]:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    bids = Bid.objects.filter(tender=tender).select_related('vendor', 'evaluation')
    
    # Sort bids by total score (highest first) if evaluated
    bids = sorted(bids, key=lambda b: getattr(b.evaluation, 'total_score', 0) if hasattr(b, 'evaluation') else -1, reverse=True)

    context = {
        'tender': tender,
        'bids': bids,
        'page_title': f'Evaluations: {tender.title}',
    }
    
    if request.user.role in [UserRole.MANAGER, UserRole.ADMIN]:
        return render(request, 'evaluations/manager_approval.html', context)
    else:
        return render(request, 'evaluations/list.html', context)


@login_required
def evaluate_bid(request, bid_id):
    """Procurement Officer scores a bid."""
    if request.user.role not in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER]:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    bid = get_object_or_404(Bid, id=bid_id)
    tender = bid.tender

    try:
        evaluation = Evaluation.objects.get(bid=bid)
    except Evaluation.DoesNotExist:
        evaluation = Evaluation(bid=bid, evaluated_by=request.user)

    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            eval_obj = form.save(commit=False)
            eval_obj.evaluated_by = request.user
            eval_obj.evaluated_at = timezone.now()
            
            # Calculate total score
            total = (
                eval_obj.price_score + 
                eval_obj.experience_score + 
                eval_obj.warranty_score + 
                eval_obj.delivery_score
            )
            eval_obj.total_score = total

            # Auto-reject if < 40
            if total < 40:
                eval_obj.status = EvaluationStatus.REJECTED
                bid.status = BidStatus.REJECTED
                messages.warning(request, f'Bid auto-rejected. Score ({total}) is below 40.')
            else:
                eval_obj.status = EvaluationStatus.COMPLETED
                bid.status = BidStatus.SHORTLISTED
                messages.success(request, f'Bid evaluated successfully. Score: {total}')
            
            eval_obj.save()
            bid.save()
            
            # Update tender status if it was OPEN or CLOSED
            if tender.status in [TenderStatus.OPEN, TenderStatus.CLOSED]:
                tender.status = TenderStatus.UNDER_EVALUATION
                tender.save()

            return redirect('evaluations:tender_evaluations', tender_id=tender.id)
    else:
        form = EvaluationForm(instance=evaluation)

    return render(request, 'evaluations/form.html', {
        'form': form,
        'bid': bid,
        'tender': tender,
        'page_title': 'Score Bid'
    })


@login_required
def submit_evaluations(request, tender_id):
    """Procurement submits all SHORTLISTED bids to Manager."""
    if request.user.role not in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER]:
        return redirect('dashboard:index')
        
    tender = get_object_or_404(Tender, id=tender_id)
    
    if request.method == 'POST':
        evaluations = Evaluation.objects.filter(bid__tender=tender, status=EvaluationStatus.COMPLETED)
        if not evaluations.exists():
            messages.error(request, 'No completed evaluations to submit.')
            return redirect('evaluations:tender_evaluations', tender_id=tender.id)
            
        evaluations.update(status=EvaluationStatus.PENDING_APPROVAL)
        
        # Log Action
        from apps.accounts.models import SystemLog, SystemLogAction
        SystemLog.objects.create(
            user=request.user,
            action=SystemLogAction.EVALUATION_SUBMITTED,
            description=f"Submitted evaluations for Tender {tender.tender_number} to Manager",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Evaluations submitted to Manager for final approval.')
        
    return redirect('evaluations:tender_evaluations', tender_id=tender.id)


@login_required
def approve_award(request, evaluation_id):
    """Manager approves one evaluation -> Bid becomes Winner."""
    if request.user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        return redirect('dashboard:index')
        
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    bid = evaluation.bid
    tender = bid.tender
    
    if request.method == 'POST':
        # Approve this evaluation
        evaluation.status = EvaluationStatus.APPROVED
        evaluation.is_winner = True
        evaluation.approved_by = request.user
        evaluation.approved_at = timezone.now()
        evaluation.save()
        
        # Mark Bid as Winner
        bid.status = BidStatus.APPROVED
        bid.save()
        
        # Mark Tender as Awarded
        tender.status = TenderStatus.AWARDED
        tender.save()
        
        # Reject all other bids for this tender
        other_bids = Bid.objects.filter(tender=tender).exclude(id=bid.id)
        other_bids.update(status=BidStatus.REJECTED)
        
        # Update other evaluations
        other_evals = Evaluation.objects.filter(bid__tender=tender).exclude(id=evaluation.id)
        other_evals.update(status=EvaluationStatus.REJECTED, is_winner=False)
        
        # Log Action
        from apps.accounts.models import SystemLog, SystemLogAction
        SystemLog.objects.create(
            user=request.user,
            action=SystemLogAction.TENDER_AWARDED,
            description=f"Awarded Tender {tender.tender_number} to {bid.vendor.company_name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Bid by {bid.vendor.company_name} has been Awarded!')
        
    return redirect('evaluations:tender_evaluations', tender_id=tender.id)
