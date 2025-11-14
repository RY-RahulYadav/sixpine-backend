from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import os

@csrf_exempt
def serve_swagger_ui(request):
    """Serve Swagger UI HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>E-Commerce API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui.css" />
        <style>
            body {
                margin: 0;
                padding: 0;
            }
            .topbar {
                display: none;
            }
            .swagger-ui .info {
                margin: 30px 0;
            }
            .swagger-ui .info .title {
                font-size: 36px;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        
        <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/api/swagger.yml',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    defaultModelsExpandDepth: 1,
                    defaultModelExpandDepth: 1,
                    docExpansion: 'list',
                    filter: true,
                    persistAuthorization: true,
                    tryItOutEnabled: true,
                });
                window.ui = ui;
            };
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content, content_type='text/html')


@csrf_exempt
def serve_swagger_yaml(request):
    """Serve the swagger.yml file"""
    try:
        swagger_file_path = os.path.join(os.path.dirname(__file__), 'swagger.yml')
        return FileResponse(open(swagger_file_path, 'rb'), content_type='application/x-yaml')
    except FileNotFoundError:
        return HttpResponse('Swagger file not found', status=404)
