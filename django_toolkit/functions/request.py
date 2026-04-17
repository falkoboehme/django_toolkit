

def get_client_ip(request):
    """
    Extract client IP address from request.
    Handles X-Forwarded-For header and direct REMOTE_ADDR.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_app_model_from_request(request):
    """
    Get the app and model from the request path. Assumes the path is in the format /app/model/ or /app/model/pk/.
    """
    path_parts = request.path.strip('/').split('/')
    if len(path_parts) < 2:
        return None, None

    app_label = path_parts[0]
    model_name = path_parts[1]
    return app_label, model_name