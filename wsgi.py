from src import app
import os


if __name__ == '__main__':
    app.run('0.0.0.0', int(os.environ.get('PORT', 5000)))
