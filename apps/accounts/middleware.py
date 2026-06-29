from django.conf import settings
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class HideNextUrlMiddleware:
    """
    Middleware that intercepts all redirects containing a '?next=' parameter.
    It removes the 'next' parameter from the URL (to keep it clean in the browser),
    stores it in the user's session, and injects it back into request.GET on the next request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Incoming Request: Reinstate 'next' from session into request.GET
        if 'next_url_hidden' in request.session:
            hidden_next = request.session.pop('next_url_hidden')
            # request.GET is immutable, so we must copy it
            mutable_get = request.GET.copy()
            mutable_get['next'] = hidden_next
            request.GET = mutable_get

        response = self.get_response(request)

        # 2. Outgoing Response: Intercept 302 redirects and hide 'next'
        if response.status_code == 302:
            redirect_url = response.url
            parsed_url = urlparse(redirect_url)
            
            query_params = parse_qs(parsed_url.query)
            
            # If there's a 'next' parameter, hide it
            if 'next' in query_params:
                # Save 'next' in session
                request.session['next_url_hidden'] = query_params['next'][0]
                
                # Rebuild the URL without 'next'
                new_query = {k: v for k, v in query_params.items() if k != 'next'}
                new_query_string = urlencode(new_query, doseq=True)
                new_url = urlunparse((
                    parsed_url.scheme, 
                    parsed_url.netloc, 
                    parsed_url.path, 
                    parsed_url.params, 
                    new_query_string, 
                    parsed_url.fragment
                ))
                
                # Update the Location header
                response['Location'] = new_url

        return response

import logging
from django.db.utils import ProgrammingError, OperationalError
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class MigrationErrorMiddleware:
    """
    Catches Database ProgrammingError and OperationalError, which usually indicate 
    that migrations have not been applied, and returns a friendly error page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except (ProgrammingError, OperationalError) as e:
            error_msg = str(e).lower()
            if "column" in error_msg or "relation" in error_msg or "does not exist" in error_msg:
                html = f"""
                <html>
                <head>
                    <title>System Update Required</title>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; color: #334155; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                        .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); max-width: 500px; text-align: center; border-top: 4px solid #ef4444; }}
                        h1 {{ color: #0f172a; font-size: 24px; margin-bottom: 16px; margin-top: 0; }}
                        p {{ line-height: 1.6; margin-bottom: 24px; }}
                        .code {{ background: #1e293b; color: #10b981; padding: 16px; border-radius: 8px; text-align: left; font-family: monospace; font-size: 14px; overflow-x: auto; }}
                        .error-details {{ margin-top: 24px; padding: 12px; background: #fee2e2; color: #991b1b; border-radius: 6px; font-size: 12px; text-align: left; word-break: break-all; }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>⚙️ Database Update Required</h1>
                        <p>The system has been upgraded with new features, but the database schema needs to be updated to match the new code.</p>
                        <p>Please run the following commands in your terminal:</p>
                        <div class="code">
                            python manage.py makemigrations<br><br>
                            python manage.py migrate
                        </div>
                        <div class="error-details">
                            <strong>Technical Detail:</strong><br>
                            {e}
                        </div>
                    </div>
                </body>
                </html>
                """
                return HttpResponse(html, status=500)
            raise

class GlobalExceptionMiddleware:
    """
    Catches unhandled exceptions, logs them, and returns a user-friendly
    error message via Django messages and redirects back, avoiding the 500 debug screen.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # We don't catch ProgrammingError or OperationalError here
        # because MigrationErrorMiddleware handles them if it runs first,
        # but if it falls through, we catch it here.
        
        # Log the error
        import traceback
        logger.error(f"Unhandled Exception at {request.path}: {str(exception)}\n{traceback.format_exc()}")
        
        from django.contrib import messages
        from django.shortcuts import redirect
        
        # If the request is an AJAX/API request, we shouldn't redirect
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
            from django.http import JsonResponse
            return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)
            
        # Add a friendly error message
        messages.error(request, "Oops! Something went wrong while processing your request. Please try again.")
        
        # Redirect back to the previous page if possible
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
            
        # If no referer, redirect to home
        return redirect('/')
