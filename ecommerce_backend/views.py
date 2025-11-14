from django.http import HttpResponse


def root_welcome(request):
    return HttpResponse("Welcome to E-Commerce server", content_type="text/plain", status=200)
