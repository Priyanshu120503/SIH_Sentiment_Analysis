from flask import Flask, jsonify
from scrapfly import *
import pandas as pd
from urllib.parse import unquote

app = Flask(__name__)


@app.route("/data/<path:link>")
def analysis_data(link):
    print(unquote(link))
    df = get_predictions(unquote(link))
    data = {
        'positive': len(df[df.rating > 3]),
        'neutral': len(df[df.rating == 3]),
        'negative': len(df[df.rating < 3])
    }
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
