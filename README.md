# Scanned Book OCR

Converts every scanned PDF in `Book/` into an LLM-friendly UTF-8 text file in `Output/`, plus `Output/OCR_Report.json`. OCR is performed locally with PaddleOCR; no cloud API or network service is used at runtime.

## Installation

Use Python 3.12 and a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install PaddlePaddle for your hardware first. For an NVIDIA GPU with CUDA 11.8 support, use:

```powershell
python -m pip install paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

For CPU-only installation, use:

```powershell
python -m pip install paddlepaddle -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

Then install the remaining dependencies:

```powershell
python -m pip install -r requirements.txt
```

Use `python -m pip`, not `uv add paddle`: the framework package is named `paddlepaddle-gpu` (or `paddlepaddle` for CPU). Verify the active environment with `python -c "import paddle; print(paddle.__version__, paddle.device.get_device())"`.

The first PaddleOCR run may download its model files. After that, inference is local; for offline deployment, pre-cache the models and prevent outbound network access.

## Usage

Put PDFs in `Book/`, then run:

```powershell
python main.py
```

Useful environment overrides include `OCR_BOOK_DIR`, `OCR_OUTPUT_DIR`, `OCR_RENDER_DPI`, `OCR_MAX_IMAGE_DIMENSION`, `OCR_USE_GPU=true`, `OCR_MAX_RETRIES=3`, `OCR_WORKERS=1`, and `OCR_LOG_LEVEL=DEBUG`. Oversized pages are automatically downscaled to avoid GPU/CPU memory exhaustion.

The cleaner removes likely repeated running headers/footers and standalone page numbers, joins wrapped lines, repairs hyphenation, and groups lines into paragraphs. OCR confidence is the mean confidence of successful detections; failed pages and heuristic warnings are retained in the report.

## Project layout

`main.py` is the CLI, `config.py` holds environment-backed settings, and `src/` contains PDF rendering, PaddleOCR integration, cleanup, reporting, and shared utilities.
