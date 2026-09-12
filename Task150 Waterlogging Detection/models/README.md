# Custom YOLO Model Weights

Place your trained YOLO11 model weights file here named `best.pt`:

```
models/best.pt
```

### Supported Custom Classes:
When training your custom YOLO model for waterlogging detection, recommended class mappings include:
- `0`: vehicle (car, bus, truck, motorcycle)
- `1`: person (pedestrian, commuter)
- `2`: waterlogging / flood zone (inundated road, standing water)

If `models/best.pt` is not present, `detect.py` will fall back to using default YOLO11 weights (`yolo11n.pt`) paired with an intelligent computer vision color-texture segmentation pipeline to highlight waterlogged road regions dynamically.
