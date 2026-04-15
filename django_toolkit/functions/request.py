

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