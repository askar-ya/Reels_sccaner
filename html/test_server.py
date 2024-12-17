from flask import Flask, render_template

app = Flask(__name__)

@app.route('/head')
def head():
    return render_template('head.html')

@app.route('/reels')
def reels():
    return render_template('reels.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)