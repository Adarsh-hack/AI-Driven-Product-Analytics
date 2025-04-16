#!/bin/bash

# Create the main app directory structure
mkdir -p app/{models,routes,services,static/{css,img,js/{charts,tracking}},templates/{auth,dashboard,landing,projects},utils}
mkdir -p instance
mkdir -p migrations/versions
mkdir -p templates

# Create __init__.py files
touch app/__init__.py
touch app/models/__init__.py
touch app/routes/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py

# Create model files
touch app/models/event.py
touch app/models/project.py
touch app/models/user.py

# Create route files
touch app/routes/auth.py
touch app/routes/dashboard.py
touch app/routes/events.py
touch app/routes/landing.py
touch app/routes/project.py

# Create service files
touch app/services/analytics.py
touch app/services/deepseek_insights.py
touch app/services/event_processing.py
touch app/services/ml_insights.py

# Create util files
touch app/utils/decorators.py
touch app/utils/validators.py

# Create static files
touch app/static/css/dashboard.css
touch app/static/css/main.css
touch app/static/img/dashboard-preview.png
touch app/static/js/charts/dashboard.js
touch app/static/js/tracking/tracker.js
touch app/static/js/main.js

# Create template files
touch app/templates/auth/login.html
touch app/templates/auth/register.html
touch app/templates/dashboard/empty.html
touch app/templates/dashboard/events.html
touch app/templates/dashboard/index.html
touch app/templates/dashboard/insights.html
touch app/templates/landing/features.html
touch app/templates/landing/index.html
touch app/templates/landing/pricing.html
touch app/templates/projects/analytics.html
touch app/templates/projects/connection_test.html
touch app/templates/projects/create.html
touch app/templates/projects/detail.html
touch app/templates/projects/edit.html
touch app/templates/projects/list.html
touch app/templates/projects/ml_insights.html
touch app/templates/base.html

# Create main app files
touch app/config.py
touch app/forms.py

# Create instance files
touch instance/analytics.db

# Create migration files
touch migrations/README
touch migrations/alembic.ini
touch migrations/env.py
touch migrations/script.py.mako

# Create root level files
touch templates/test_analytics.html
touch app.py
touch create_db.py
touch fix_db_permissions.py
touch product_analytics.db
touch requirements.txt
touch run.py
touch test_website.py

echo "Project structure created successfully!"