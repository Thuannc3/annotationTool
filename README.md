# 🖌️ Contour Annotation Tool

## 📖 Overview
**Contour Annotation Tool** is an image annotation software that supports **multi-contour labeling**.  
Users can:
- Create, edit, move, and delete points on an image.  
- Switch between straight line and curved contour modes.  
- Assign layer values to create **mask images** for AI training or image processing.  
- Save and load contours in JSON format.

---

## ⚙️ Environment Setup (If you want to run by python)

### 1️⃣ Create Virtual Environment
```bash
python -m venv .venv
```

### 2️⃣ Activate Virtual Environment
- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```
- **Linux/macOS:**
  ```bash
  source .venv/bin/activate
  ```

### 3️⃣ Install Required Packages
```bash
pip install -r requirement.txt
```

---

## ▶️ Run the Application

Double click to

```bash
tooldraw.exe
```
or run
```bash
python tooldraw.py
```

Once launched, the main interface will appear, including:  
- **Control toolbar (Zoom, Hand, Add Contour, Annotate...)**  
- **Main image viewer**  
- **Contour coordinate table**

---

## 🖱️ User Guide

### 🔹 Basic Operations
| Action | Function |
|---------|-----------|
| **File → Load Image** | Open the image to annotate |
| **File → Save Contours** | Save contours to JSON file |
| **File → Load Contours** | Load existing contours from JSON |
| **Right-click on image** | Add a point to current contour |
| **Left-click + drag** | Move a point |
| **Hand Mode** | Pan the image |
| **Zoom In / Zoom Out** | Scale the image view |
| **Annotate** | Toggle between raw image and mask |
| **Base Value / Layer Value** | Set pixel values for base/mask |
| **Add Contour** | Create a new contour |
| **Delete Selected Point** | Remove the selected point |

### 🔹 Drawing Modes
- **Line**: Connects points with straight lines.  
- **Curve**: Draws smooth Bezier curves between three points.

---

## 💾 Saving and Loading Data

### Contour JSON Example
```json
[
  {
    "name": "Contour 1",
    "points": [{"x":100, "y":150, "mode":"line"}],
    "layer_value": 255,
    "mode": "line"
  }
]
```

### Annotated Image
Saved as a **PNG file** containing the mask layer values.

---

## 🧩 System Requirements
- Python **3.6.8**
- Dependencies from `requirement.txt`:
  ```
  QtPy==2.0.1
  numpy==1.19.5
  json5==0.9.16
  jsonschema==3.2.0
  PyQt5==5.9
  opencv-python==4.5.5.64
  ```

---

## 🧑‍💻 Author
**Thuan** – Embedded Engineer

---
