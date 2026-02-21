from django.urls import path, include

urlpatterns = [
    path('api/', include('analyzer.urls')),
]
# ```

# ---

# **What this does:**

# Any request to `http://localhost:8000/api/analyze/` will go to our `analyze_papers` view.

# Your API endpoints will be:
# ```
# POST http://localhost:8000/api/analyze/   ← upload PDFs, get results
# GET  http://localhost:8000/api/health/    ← check if server is running