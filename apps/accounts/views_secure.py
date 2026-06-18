from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404, HttpResponseRedirect
from django.apps import apps
from django.shortcuts import get_object_or_404
import cloudinary.utils

@login_required
def secure_document_download(request, app_label, model_name, document_id, field_name):
    """
    Generates a temporary, signed Cloudinary URL for authenticated files.
    Ensures that only authorized users can download specific documents.
    """
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        raise Http404("Model not found")

    obj = get_object_or_404(model, id=document_id)
    
    # ─── ACCESS CONTROL ──────────────────────────────────────────────
    user = request.user
    is_staff = user.role in ['admin', 'manager', 'procurement_officer'] or user.is_staff

    if model_name.lower() == 'bid':
        # Only staff or the vendor who placed the bid can view it
        if not (is_staff or (hasattr(obj, 'vendor') and obj.vendor.user == user)):
            return HttpResponseForbidden("You do not have permission to view this bid document.")
            
    elif model_name.lower() == 'vendor':
        # Only staff or the vendor themselves can view their verification docs
        if not (is_staff or obj.user == user):
            return HttpResponseForbidden("You do not have permission to view this vendor document.")
            
    elif model_name.lower() == 'tender':
        # Tenders are public for all logged in users, but can restrict Drafts
        if getattr(obj, 'status', '') == 'draft' and not is_staff:
             return HttpResponseForbidden("This tender is not published yet.")

    # ─── GENERATE SIGNED URL ─────────────────────────────────────────
    file_field = getattr(obj, field_name, None)
    if not file_field or not file_field.name:
        raise Http404("Document not found")
        
    try:
        url, options = cloudinary.utils.cloudinary_url(
            file_field.name,
            resource_type="raw",
            type="authenticated",
            sign_url=True,
            # URL expires implicitly based on Cloudinary account settings
        )
        return HttpResponseRedirect(url)
    except Exception as e:
        raise Http404(f"Could not generate secure URL. Please ensure Cloudinary is configured.")
