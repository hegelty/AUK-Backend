from flask import Flask, request
from route.column import get_column
from route.score import upload_score_2
app = Flask(__name__)


@app.route('/column')
def column(id=None):
    return get_column(id)


@app.route('/upload_score', methods=['POST'])
def upload_score():
    uid = request.form['id']
    score = request.form['score']
    return upload_score_2(uid, score)


if __name__ == '__main__':
    app.run()
