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
