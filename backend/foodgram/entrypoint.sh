#!/bin/sh

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Loading initial data"
if python manage.py shell -c "from recipes.models import Ingredient; exit(0) if Ingredient.objects.exists() else exit(1)"; then
    echo "Ingredients table is not empty - skipping fixture loading"
else
    echo "Loading ingredients fixture..."
    python manage.py loaddata ingredients_fixture.json
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 foodgram.wsgi