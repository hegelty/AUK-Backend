from flask import Flask, request
from route.column import ColumnsUnavailable, get_column
from route.score import upload_score_2
app = Flask(__name__)


@app.route('/column')
def column():
    index = request.args.get('id', '0')
    if not index.isascii() or not index.isdecimal() or len(index) > 9:
        return {'error': 'invalid column index'}, 400
    try:
        return get_column(int(index))
    except IndexError:
        return {'error': 'column not found'}, 404
    except ColumnsUnavailable:
        return {'error': 'columns temporarily unavailable'}, 503


@app.route('/upload_score', methods=['POST'])
def upload_score():
    uid = request.form['id']
    score = request.form['score']
    return upload_score_2(uid, score)


if __name__ == '__main__':
    print(1)
    app.run(port=8889)
