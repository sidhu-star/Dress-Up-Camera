# Dress Up Camera V2 — Real AI Try-On

V2 connects the web UI to FASHN's hosted **Try-On Max** model. This is a generative image workflow, not a live-video filter. It produces a realistic still image from a photo of a person and product images.

## 1. Get an API key

Create an API key in the [FASHN Developer API dashboard](https://app.fashn.ai/api). Usage is credit-based; review the provider's current pricing before generating outfits.

## 2. Start the backend

From the repository root:

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and replace `FASHN_API_KEY` with your private key. Never paste the key into browser code or commit the real `.env` file.

Start the API:

```bash
uvicorn main:app --reload --port 8000
```

Check [http://localhost:8000/api/health](http://localhost:8000/api/health). It should show `"provider_configured": true`.

## 3. Start the frontend

In a second terminal at the repository root:

```bash
python -m http.server 5500
```

Open [http://localhost:5500/v2.html](http://localhost:5500/v2.html).

The browser will use `http://localhost:8000` for the API by default. If you deploy the backend elsewhere, set the API base before loading V2 in the browser:

```js
localStorage.setItem("duc-api-base", "https://YOUR-BACKEND-DOMAIN")
```

Reload the page after setting it.

## Whole Outfit behavior

The provider endpoint accepts one product image per prediction. V2 applies items sequentially: each generated result becomes the person image for the next item. This is real AI generation for each item, but it is not a single joint multi-garment diffusion pass. The order can affect results and small details may drift. Use up to five items per outfit. For stronger joint outfit consistency, a future backend should use a model that explicitly supports multi-garment conditioning in one pass.

## Privacy and safety

The selected person photo and clothing images are sent to the configured provider for processing. Use only photos you have permission to upload. Don't expose the API key in frontend code. Add authentication, rate limiting, HTTPS, and a restrictive `CORS_ORIGINS` value before a public deployment.

## Troubleshooting

- **AI server not connected:** start the FastAPI backend on port 8000.
- **Server needs API key:** edit `backend/.env`, restart the backend.
- **Camera blocked:** use localhost/HTTPS and allow camera permission.
- **Provider error:** verify the key, account credits, input image size, and provider status.
- **URL input:** V1 stores product links; V2 currently asks you to upload the product image itself because shopping sites often block direct image extraction.
