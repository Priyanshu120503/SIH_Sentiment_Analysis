from flask import Flask, jsonify
from scrapfly import *
from urllib.parse import unquote

app = Flask(__name__)


@app.route("/data/<path:link>")
def analysis_data(link):
    print(unquote(link))
    df = get_predictions(unquote(link))
    make_word_cloud(df['Comment'].sum())
    data = {
        'positive': len(df[df.rating > 3]),
        'neutral': len(df[df.rating == 3]),
        'negative': len(df[df.rating < 3]),
        'comment_sentiments': []
    }

    for i, row in df.iterrows():
        data['comment_sentiments'].append({
            'comment': row['Comment'],
            'like_count': row['likeCount'],
            'sentiment': 1 if row['rating'] > 3 else (0 if row['rating'] == 3 else -1)
        })

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
