import sqlite3

from flask import Flask, request

from route.column import ColumnsUnavailable, get_column
from route.score import store_score

app = Flask(__name__)
app.config["SCORE_DATABASE"] = "score.db"


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
    uid = request.form.get('id', '').strip()
    raw_score = request.form.get('score', '')
    if not uid or len(uid) > 128 or not raw_score.isascii() or not raw_score.isdecimal() or len(raw_score) > 3:
        return 'fail', 400
    score = int(raw_score)
    if score > 100:
        return 'fail', 400
    try:
        store_score(app.config['SCORE_DATABASE'], uid, score)
    except sqlite3.Error:
        app.logger.exception("Could not store the daily score")
        return 'fail', 503
    return 'success'


if __name__ == '__main__':
    print(1)
    app.run(port=8889)
