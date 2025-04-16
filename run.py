from app import create_app, db
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Create a shell context for Flask CLI to access the app and db objects
    """
    return {'app': app, 'db': db}

if __name__ == '__main__':
    app.run(debug=True)