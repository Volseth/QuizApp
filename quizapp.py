from quizapp import app
from quizapp import db

if __name__ == '__main__':
    # Create database tables
    db.create_all()
    # Application server run
    app.run(debug=True, use_reloader=False)
