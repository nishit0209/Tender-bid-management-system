"""
Evaluation Model — Evaluations App
Enterprise Tender & Bid Management System

Scoring: Price=40, Experience=30, Warranty=20, Delivery=10 (Total=100)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import TimeStampedModel
from apps.bids.models import Bid


# ─────────────────────────────────────────────
# Choices
# ─────────────────────────────────────────────
class EvaluationStatus(models.TextChoices):
    DRAFT            = 'draft',            _('Draft')
    COMPLETED        = 'completed',        _('Evaluation Completed')
    PENDING_APPROVAL = 'pending_approval', _('Pending Manager Approval')
    APPROVED         = 'approved',         _('Approved by Manager')
    REJECTED         = 'rejected',         _('Rejected — Re-evaluate')


# ─────────────────────────────────────────────
# Custom Manager
# ─────────────────────────────────────────────
class EvaluationManager(models.Manager):

    def for_tender(self, tender):
        return self.filter(bid__tender=tender)

    def ranked(self, tender):
        """Returns evaluations for a tender ordered by total score descending."""
        return self.filter(
            bid__tender=tender,
            status=EvaluationStatus.COMPLETED,
        ).order_by('-total_score')

    def winners(self):
        return self.filter(is_winner=True)

    def pending_approval(self):
        return self.filter(status=EvaluationStatus.PENDING_APPROVAL)


# ─────────────────────────────────────────────
# Evaluation Model
# ─────────────────────────────────────────────
class Evaluation(TimeStampedModel):
    """
    Evaluation scores for a bid.
    Each bid has exactly one evaluation record.

    Scoring Breakdown:
    - Price Score:      0 – 40 marks
    - Experience Score: 0 – 30 marks
    - Warranty Score:   0 – 20 marks
    - Delivery Score:   0 – 10 marks
    - Total Score:      0 – 100 marks (computed, stored for performance)
    """

    bid               = models.OneToOneField(
                            Bid,
                            on_delete=models.CASCADE,
                            related_name='evaluation',
                        )

    # ── Individual Scores ──────────────────────
    price_score       = models.DecimalField(
                            max_digits=5, decimal_places=2,
                            validators=[MinValueValidator(0), MaxValueValidator(40)],
                            verbose_name=_('Price Score (0-40)'),
                            help_text='Higher score = more competitive price',
                        )
    experience_score  = models.DecimalField(
                            max_digits=5, decimal_places=2,
                            validators=[MinValueValidator(0), MaxValueValidator(30)],
                            verbose_name=_('Experience Score (0-30)'),
                            help_text='Years of relevant experience and past performance',
                        )
    warranty_score    = models.DecimalField(
                            max_digits=5, decimal_places=2,
                            validators=[MinValueValidator(0), MaxValueValidator(20)],
                            verbose_name=_('Warranty Score (0-20)'),
                            help_text='Duration and coverage of warranty offered',
                        )
    delivery_score    = models.DecimalField(
                            max_digits=5, decimal_places=2,
                            validators=[MinValueValidator(0), MaxValueValidator(10)],
                            verbose_name=_('Delivery Score (0-10)'),
                            help_text='Speed and reliability of proposed delivery timeline',
                        )

    # ── Stored Total Score (computed on save) ──
    total_score       = models.DecimalField(
                            max_digits=6, decimal_places=2,
                            default=0,
                            db_index=True,
                        )

    # ── Ranking ────────────────────────────────
    rank              = models.PositiveIntegerField(
                            null=True, blank=True,
                            help_text='Rank among all evaluated bids for this tender (1=best)',
                        )

    # ── Evaluation Notes ───────────────────────
    price_remarks     = models.TextField(blank=True, null=True)
    experience_remarks= models.TextField(blank=True, null=True)
    warranty_remarks  = models.TextField(blank=True, null=True)
    delivery_remarks  = models.TextField(blank=True, null=True)
    recommendation    = models.TextField(
                            blank=True, null=True,
                            help_text='Evaluator\'s recommendation for this bid',
                        )
    overall_remarks   = models.TextField(blank=True, null=True)

    # ── Winner Flag ────────────────────────────
    is_winner         = models.BooleanField(default=False, db_index=True)

    # ── Status & Workflow ───────────────────────
    status            = models.CharField(
                            max_length=20,
                            choices=EvaluationStatus.choices,
                            default=EvaluationStatus.DRAFT,
                            db_index=True,
                        )

    # ── Staff Tracking ──────────────────────────
    evaluated_by      = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.PROTECT,
                            related_name='evaluations_done',
                        )
    evaluated_at      = models.DateTimeField(null=True, blank=True)
    approved_by       = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='evaluations_approved',
                        )
    approved_at       = models.DateTimeField(null=True, blank=True)
    approval_remarks  = models.TextField(blank=True, null=True)

    objects = EvaluationManager()

    class Meta:
        verbose_name        = _('Bid Evaluation')
        verbose_name_plural = _('Bid Evaluations')
        ordering            = ['-total_score']
        indexes = [
            models.Index(fields=['total_score']),
            models.Index(fields=['is_winner']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (
            f"Evaluation — {self.bid.vendor.company_name} "
            f"for {self.bid.tender.tender_number} "
            f"[Score: {self.total_score}/100]"
        )

    # ── Score Calculation ──────────────────────
    def calculate_total(self):
        """Compute total score from individual components."""
        return (
            (self.price_score or 0)
            + (self.experience_score or 0)
            + (self.warranty_score or 0)
            + (self.delivery_score or 0)
        )

    @property
    def price_percentage(self):
        return float(self.price_score / 40 * 100) if self.price_score else 0

    @property
    def experience_percentage(self):
        return float(self.experience_score / 30 * 100) if self.experience_score else 0

    @property
    def warranty_percentage(self):
        return float(self.warranty_score / 20 * 100) if self.warranty_score else 0

    @property
    def delivery_percentage(self):
        return float(self.delivery_score / 10 * 100) if self.delivery_score else 0

    @property
    def total_percentage(self):
        return float(self.total_score)

    @property
    def grade(self):
        """Letter grade based on total score."""
        score = float(self.total_score)
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        else:
            return 'D'

    @classmethod
    def calculate_price_score(cls, bid_amount, min_bid_amount, max_marks=40):
        """
        Auto-calculate price score:
        Lowest bid gets full marks. Others are proportionally scored.
        Score = (min_bid / bid_amount) * max_marks
        """
        if not bid_amount or bid_amount <= 0:
            return 0
        score = (min_bid_amount / bid_amount) * max_marks
        return min(round(score, 2), max_marks)

    @classmethod
    def assign_ranks_for_tender(cls, tender):
        """
        Recalculate and assign ranks to all completed evaluations for a tender.
        Rank 1 = highest total score.
        """
        evaluations = cls.objects.filter(
            bid__tender=tender,
            status__in=[EvaluationStatus.COMPLETED, EvaluationStatus.APPROVED],
        ).order_by('-total_score')

        for idx, evaluation in enumerate(evaluations, start=1):
            evaluation.rank = idx
            evaluation.save(update_fields=['rank', 'updated_at'])

    def save(self, *args, **kwargs):
        # Recompute total score before every save
        self.total_score = self.calculate_total()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('evaluations:detail', kwargs={'pk': self.pk})
