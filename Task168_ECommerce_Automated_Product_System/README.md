\# Task 168 — E-Commerce Automated Product System



\## 📌 Project Overview



The \*\*E-Commerce Automated Product System\*\* is a computer-vision-based automation project designed to process product images and generate useful product assets and metadata for an e-commerce workflow.



The system uses \*\*SAM 2 (Segment Anything Model 2)\*\* for product segmentation. Given a product image and a selected bounding box, SAM 2 generates a segmentation mask for the product. The generated mask can then be used for further image-processing operations such as transparent-background generation, studio-style image generation, image resizing, and product catalog preparation.



The project is designed as an automated pipeline that reduces the amount of manual work required when preparing product images for an e-commerce platform.



\---



\## 🎯 Objectives



The main objectives of this project are:



\* Detect and isolate a product from its background.

\* Generate an accurate segmentation mask using SAM 2.

\* Create transparent product images.

\* Generate processed/studio-style product images.

\* Generate multiple image resolutions.

\* Store product information in a structured product catalog.

\* Normalize product metadata.

\* Perform product-image compliance checks.

\* Automate product-image processing using Python scripts.



\---



\## 🧠 Technologies Used



\### Python



Python is used as the primary programming language for the image-processing and machine-learning pipeline.



\### SAM 2



\*\*Segment Anything Model 2 (SAM 2)\*\* is used for promptable image segmentation.



The official SAM 2 project is developed by Meta AI Research / FAIR. SAM 2 supports image and video segmentation and accepts prompts such as points and bounding boxes.



\*\*Official SAM 2 repository:\*\*



\[Meta SAM 2 — Official GitHub Repository](https://github.com/facebookresearch/sam2?utm\_source=chatgpt.com)



\*\*Official Meta SAM 2 research page:\*\*



\[Meta AI — SAM 2](https://ai.meta.com/research/sam2/?utm\_source=chatgpt.com)



\### PyTorch



PyTorch is used to load and execute the SAM 2 model.



The application automatically checks whether CUDA is available:



```python

device = "cuda" if torch.cuda.is\_available() else "cpu"

```



If a CUDA-compatible GPU is unavailable, the system runs on the CPU.



\### NumPy



NumPy is used for image arrays, bounding boxes, masks, and numerical processing.



\### Pillow



Pillow (`PIL`) is used for reading, converting, and saving images.



\### CSV / JSON



CSV and JSON files are used to store product information and metadata.



\---



\## 🤖 SAM 2 Model and Checkpoint



This project uses the \*\*original SAM 2 Hiera Small checkpoint\*\*:



```text

sam2\_hiera\_small.pt

```



The official SAM 2 repository provides the original SAM 2 Hiera checkpoints, including:



\* `sam2\_hiera\_tiny.pt`

\* `sam2\_hiera\_small.pt`

\* `sam2\_hiera\_base\_plus.pt`

\* `sam2\_hiera\_large.pt`



The repository also provides newer \*\*SAM 2.1\*\* checkpoints. This project currently uses the original `sam2\_hiera\_small.pt` checkpoint, so the model configuration and checkpoint should remain matched.



\### Official Model Resources



\*\*SAM 2 source code and checkpoint information:\*\*



\[Official SAM 2 GitHub Repository](https://github.com/facebookresearch/sam2?utm\_source=chatgpt.com)



\*\*Official Meta SAM 2 page:\*\*



\[Official Meta SAM 2 Research Page](https://ai.meta.com/research/sam2/?utm\_source=chatgpt.com)



The official repository's \*\*Download Checkpoints\*\* section contains the available checkpoint downloads.



\### Checkpoint Used in This Project



The project expects the checkpoint at:



```text

checkpoints/

└── sam2\_hiera\_small.pt

```



The checkpoint is intentionally kept separately from the SAM 2 source-code directory.



\---



\## 📂 Project Structure



```text

Task168\_ECommerce\_Automated\_Product\_System/

│

├── checkpoints/

│   └── sam2\_hiera\_small.pt

│

├── images/

│   ├── headphone.png

│   ├── headphone\_studio.png

│   ├── headphone\_transparent.png

│   ├── product3.jpg

│   ├── product3\_transparent.png

│   ├── product\_metadata.json

│   ├── sam\_mask\_headphone.png

│   ├── shoe\_mask.png

│   ├── shoe\_metadata.json

│   ├── shoe\_studio.png

│   │

│   └── resized/

│       ├── product\_400x400.jpg

│       ├── product\_600x600.jpg

│       └── product\_800x800.jpg

│

├── sam2/

│   └── sam2/

│       ├── build\_sam.py

│       ├── sam2\_image\_predictor.py

│       ├── \_\_init\_\_.py

│       │

│       ├── configs/

│       │   └── sam2/

│       │       ├── sam2\_hiera\_b+.yaml

│       │       ├── sam2\_hiera\_l.yaml

│       │       ├── sam2\_hiera\_s.yaml

│       │       └── sam2\_hiera\_t.yaml

│       │

│       ├── modeling/

│       │   ├── backbones/

│       │   └── sam/

│       │

│       └── utils/

│

├── scripts/

│   ├── ask\_vlm.py

│   ├── check\_compliance.py

│   ├── create\_product\_csv.py

│   ├── create\_resolutions.py

│   ├── create\_studio\_image.py

│   ├── create\_transparent.py

│   ├── get\_box.py

│   ├── normalize\_metadata.py

│   └── sam\_segment.py

│

└── product\_catalog.csv

```



\---



\## 🔄 Overall Processing Workflow



The automated workflow can be summarized as:



```text

Product Image

&#x20;     ↓

Product Bounding Box

&#x20;     ↓

SAM 2 Segmentation

&#x20;     ↓

Generate Multiple Candidate Masks

&#x20;     ↓

Select Highest-Confidence Mask

&#x20;     ↓

Create Product Mask

&#x20;     ↓

Remove Background

&#x20;     ↓

Generate Transparent Image

&#x20;     ↓

Generate Studio Image

&#x20;     ↓

Generate Multiple Resolutions

&#x20;     ↓

Normalize Metadata

&#x20;     ↓

Compliance Checking

&#x20;     ↓

Product Catalog

```



\---



\## 🖼️ SAM 2 Product Segmentation



The main segmentation script loads the product image and SAM 2 model.



The project determines its base directory dynamically:



```python

BASE\_DIR = Path(\_\_file\_\_).resolve().parent.parent

```



The input image is located using:



```python

image\_path = BASE\_DIR / "images" / "product3.jpg"

```



The checkpoint is located using:



```python

checkpoint = BASE\_DIR / "checkpoints" / "sam2\_hiera\_small.pt"

```



The SAM 2 configuration is:



```text

sam2/sam2/configs/sam2/sam2\_hiera\_s.yaml

```



The model is loaded using:



```python

sam2\_model = build\_sam2(

&#x20;   str(model\_cfg),

&#x20;   str(checkpoint),

&#x20;   device=device

)

```



\---



\## 📦 Bounding Box Based Segmentation



The product bounding box is obtained using the project's `get\_box.py` script:



```python

from get\_box import get\_product\_box



box = np.array(get\_product\_box())

```



The bounding box is then provided to the SAM 2 image predictor:



```python

masks, scores, logits = predictor.predict(

&#x20;   box=box,

&#x20;   multimask\_output=True

)

```



SAM 2 generates multiple candidate masks and corresponding confidence scores.



The system selects the mask with the highest confidence:



```python

best\_index = np.argmax(scores)



best\_mask = masks\[best\_index]

```



The selected mask is converted into an image:



```python

mask = (best\_mask \* 255).astype(np.uint8)



mask\_image = Image.fromarray(mask)

```



The resulting mask is saved inside the `images` directory.



\---



\## 🎨 Generated Product Assets



\### Product Mask



The segmentation mask identifies the pixels belonging to the product.



Example:



```text

images/shoe\_mask.png

```



\### Transparent Product Image



The generated mask can be used to remove the original background and create a transparent product image.



Example:



```text

images/product3\_transparent.png

```



\### Studio Product Image



The processed product can be placed into a studio-style image.



Example:



```text

images/shoe\_studio.png

```



\### Resized Product Images



The project generates product images at multiple resolutions:



```text

400 × 400

600 × 600

800 × 800

```



These images can be used for different e-commerce display requirements.



\---



\## 📊 Product Catalog



Product information is stored in:



```text

product\_catalog.csv

```



The catalog provides a structured way to maintain information about the processed products.



Additional product metadata is stored in JSON files such as:



```text

images/product\_metadata.json

images/shoe\_metadata.json

```



This separates structured product information from the actual image files.



\---



\## 📜 Project Scripts



\### `sam\_segment.py`



Performs product segmentation using SAM 2.



Responsibilities include:



\* Loading the product image.

\* Loading the SAM 2 checkpoint.

\* Loading the SAM 2 configuration.

\* Selecting CPU or GPU.

\* Obtaining the product bounding box.

\* Generating candidate masks.

\* Comparing mask confidence scores.

\* Selecting the best mask.

\* Saving the final segmentation mask.



\### `get\_box.py`



Obtains the bounding box used to prompt SAM 2.



\### `create\_transparent.py`



Uses the product segmentation result to generate a transparent-background product image.



\### `create\_studio\_image.py`



Creates a studio-style processed product image.



\### `create\_resolutions.py`



Creates product images at different resolutions.



\### `create\_product\_csv.py`



Creates or updates the product catalog CSV.



\### `normalize\_metadata.py`



Processes and normalizes product metadata.



\### `check\_compliance.py`



Performs product-image/content compliance checks.



\### `ask\_vlm.py`



Provides functionality related to obtaining information about product images using a vision-language model.



\---



\## ⚙️ CPU and GPU Support



The project automatically determines whether CUDA is available:



```python

device = "cuda" if torch.cuda.is\_available() else "cpu"

```



If a CUDA-compatible GPU is available:



```text

cuda

```



is selected.



Otherwise:



```text

cpu

```



is selected.



GPU execution is recommended for faster SAM 2 inference.



CPU execution can be used for testing and development.



\---



\## 🚀 Running the Project



\### 1. Enter the project directory



```powershell

cd Task168\_ECommerce\_Automated\_Product\_System

```



\### 2. Activate the Python environment



Activate the Python virtual environment configured for the project.



\### 3. Install dependencies



Install the required dependencies according to the project's dependency configuration.



The official SAM 2 repository recommends Python 3.10 or newer and provides its installation instructions in the official repository.



\### 4. Verify the checkpoint



Make sure the following file exists:



```text

checkpoints/sam2\_hiera\_small.pt

```



\### 5. Verify the input image



The current segmentation script expects:



```text

images/product3.jpg

```



\### 6. Run the segmentation script



From the project directory:



```powershell

python scripts/sam\_segment.py

```



The generated mask will be saved in the `images` directory.



\---



\## 🔍 Segmentation Example



The segmentation process can be summarized as:



```text

product3.jpg

&#x20;    ↓

Bounding Box

&#x20;    ↓

SAM 2 Image Predictor

&#x20;    ↓

Multiple Candidate Masks

&#x20;    ↓

Confidence Scores

&#x20;    ↓

Highest-Confidence Mask

&#x20;    ↓

shoe\_mask.png

```



The resulting mask can then be used by subsequent image-processing stages.



\---



\## 🛒 E-Commerce Use Case



The system can be integrated into an automated product-onboarding workflow.



A typical workflow is:



```text

Seller uploads product image

&#x20;         ↓

Image validation

&#x20;         ↓

Product segmentation

&#x20;         ↓

Background removal

&#x20;         ↓

Transparent image generation

&#x20;         ↓

Studio image generation

&#x20;         ↓

Image resizing

&#x20;         ↓

Metadata normalization

&#x20;         ↓

Compliance checking

&#x20;         ↓

Product catalog generation

&#x20;         ↓

Ready for e-commerce listing

```



This workflow reduces repetitive manual image-editing tasks and helps create consistent product assets.



\---



\## ⚠️ Important Notes



\* The SAM 2 checkpoint is required for model inference.

\* The checkpoint and configuration must correspond to the same SAM 2 model version.

\* This project currently uses the original `sam2\_hiera\_small.pt` checkpoint.

\* Do not replace the original SAM 2 checkpoint with a SAM 2.1 checkpoint unless the corresponding SAM 2.1 code and configuration are also used.

\* The input image must exist before running the segmentation script.

\* CPU inference can be considerably slower than GPU inference.

\* Generated images should be reviewed before being used in a production e-commerce system.

\* The SAM 2 source files included in this project are used by the segmentation pipeline.



\---



\## 📚 Official References



\### SAM 2 GitHub



\[facebookresearch/sam2 — Official SAM 2 Repository](https://github.com/facebookresearch/sam2?utm\_source=chatgpt.com)



\### Meta AI SAM 2



\[Meta AI — Segment Anything Model 2](https://ai.meta.com/research/sam2/?utm\_source=chatgpt.com)



\### SAM 2 Research Paper



\[SAM 2 Research Paper — arXiv](https://arxiv.org/abs/2408.00714?utm\_source=chatgpt.com)



The official repository provides the SAM 2 source code, checkpoint information, installation instructions, examples, and model documentation.



\---



\## 📄 License



SAM 2 is released by Meta under the Apache 2.0 license for the model checkpoints, SAM 2 demo code, and training code, according to the official repository.



Please refer to the official SAM 2 repository for the complete licensing information.



\---



\## 👨‍💻 Project Information



\*\*Task:\*\* 168 — E-Commerce Automated Product System



\*\*Primary Language:\*\* Python



\*\*Computer Vision Model:\*\* Meta Segment Anything Model 2 (SAM 2)



\*\*Model Variant Used:\*\* SAM 2 Hiera Small



\*\*Main Application:\*\* Automated product-image processing for e-commerce workflows



