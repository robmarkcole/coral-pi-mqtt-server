# USAGE
# Start the server:
# 	python3 coral-app.py
# Submit a request via cURL:
# 	curl -X POST -F image=@face.jpg 'http://localhost:5000/predict'
# Submita a request via Python:
# 	python simple_request.py

# import the necessary packages
from edgetpu.detection.engine import DetectionEngine
from PIL import Image
import flask
import io

# initialize our Flask application and the Keras model
app = flask.Flask(__name__)
engine = None
labels = None

MODEL = "/home/robin/edgetpu/all_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
LABEL_FILE = "/home/robin/edgetpu/all_models/coco_labels.txt"


# Function to read labels from text files.
def ReadLabelFile(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        ret = {}
        for line in lines:
            pair = line.strip().split(maxsplit=1)
            ret[int(pair[0])] = pair[1].strip()
    return ret


def load_model():
    """
    Load model and labels.
    """
    global engine, labels
    engine = DetectionEngine(MODEL)
    print(f"\n Loaded engine with model : {MODEL}")

    labels = ReadLabelFile(LABEL_FILE)
    print(f"\n Loaded labels from file : {LABEL_FILE}")
    return


@app.route("/")
def info():
    info_str = "Flask app exposing tensorflow models via Google Coral."
    return info_str


@app.route("/predict", methods=["POST"])
def predict():
    data = {"success": False}

    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            # read the image in PIL format
            image_file = flask.request.files["image"]
            print(image_file)
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes))  # PIL img object.

            # Run inference.
            predictions = engine.DetectWithImage(
                image,
                threshold=0.05,
                keep_aspect_ratio=True,
                relative_coord=False,
                top_k=10,
            )

            if predictions:
                data["success"] = True
                preds = []
                for prediction in predictions:
                    preds.append(
                        {
                            "score": str(prediction.score),
                            "label_id": str(prediction.label_id),
                            "label": labels[prediction.label_id],
                            "bounding_box": str(prediction.bounding_box),
                        }
                    )
                data["predictions"] = preds

    # return the data dictionary as a JSON response
    return flask.jsonify(data)


if __name__ == "__main__":
    load_model()
    app.run(host="0.0.0.0", port=5000)
