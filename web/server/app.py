"""Flask web server for serving lie_detector predictions"""

from flask import Flask, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
# from flask_socketio import SocketIO, emit
import os
import sys
import time
sys.path.insert(0, './')
sys.path.insert(0, '../')
from lie_detector.predict import predict_example

from tensorflow.keras import backend

ALLOWED_EXTENSIONS = set(['mp4'])


app = Flask(__name__)
cors = CORS(app)

# socketio = SocketIO(app)

app.config['UPLOAD_FOLDER'] = '/tmp'

# Tensorflow bug: https://github.com/keras-team/keras/issues/2397
# with backend.get_session().graph.as_default() as _:
#     predictor = LinePredictor()  # pylint: disable=invalid-name
    # predictor = LinePredictor(dataset_cls=IamLinesDataset)

# Sanity check.
@app.route('/')
def index():
    return 'Flask server up and running!'

@app.route('/test')
def test():
    return 'Also up and running.'



@app.route('/predict', methods=['POST'])
@cross_origin()
def face_percent():
    # socketio.emit('stage', 'video upload protocol')
    vpath = _load_video()
    percent = predict_example(vpath)#, socketio)
    
    response = jsonify({'percent': float(percent)})
    # response.headers['Access-Control-Allow-Credentials'] = True
    # response.headers['Access-Control-Allow-Origin'] = 'http://canyoudeceive.me'
    # response.headers['Access-Control-Allow-Headers'] = '*'
    return response

def _allowed_file(fname):
    return '.' in fname and fname.split('.')[1].lower() in ALLOWED_EXTENSIONS


def _load_video():

    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
            return None
        file = request.files['file']
        if file.filename == '':
            print('No selected file')
            return None
        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(fpath)

            return fpath


# def main():
#     socketio.run(app, debug=False, host='0.0.0.0', port=8000)  # nosec


# if __name__ == '__main__':
#     main()