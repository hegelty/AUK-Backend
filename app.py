from flask import Flask
from route.column import get_column
app = Flask(__name__)


@app.route('/column')
def column(id=None):
    return get_column(id)


if __name__ == '__main__':
    app.run()
