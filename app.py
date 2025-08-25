import os
from flask import Flask, render_template, request, redirect, send_from_directory, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret"  # needed for flash messages

# Upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- Home / Dashboard ----------------
@app.route("/")
def index():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    total_size = sum(os.path.getsize(os.path.join(app.config["UPLOAD_FOLDER"], f)) for f in files)
    storage_mb = round(total_size / (1024 * 1024), 2)  # convert bytes to MB
    return render_template(
        "index.html",
        files=files,
        count=len(files),
        storage=storage_mb
    )


# ---------------- Upload ----------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file selected!")
        return redirect("/")
    file = request.files["file"]
    if file.filename == "":
        flash("No file selected!")
        return redirect("/")
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    flash("✅ File uploaded successfully!")
    return redirect("/")


# ---------------- Download ----------------
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# ---------------- Delete ----------------
@app.route("/delete/<filename>")
def delete_file(filename):
    try:
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        flash("🗑️ File deleted successfully!")
    except FileNotFoundError:
        flash("⚠️ File not found!")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
