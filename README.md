# Dress Up Camera

AI-ready virtual try-on and whole-outfit builder.

## V1
- Live phone/laptop camera preview
- MediaPipe pose tracking
- Individual clothing categories
- Whole Outfit mode
- Upload clothing images
- Demo clothing overlays
- Product-link saving
- Upload-a-photo mode
- Capture/download preview
- Local browser persistence
- Responsive mobile/desktop UI

## Run
This is a static app. In VS Code, use Live Server, or run: python -m http.server 5500
Then open http://localhost:5500

Camera access requires localhost or HTTPS.

## V1 limitation
This version uses pose-aware image overlays. It is not yet a photorealistic generative virtual try-on system. Transparent PNG clothing gives the best result.

## V2 architecture
Camera/photo -> person segmentation + pose -> clothing extraction -> generative virtual try-on -> rendered result.

For Whole Outfit, support multiple garments in one inference request or a compatible multi-garment VTON pipeline.

## Product links
V1 stores shopping links as metadata. Arbitrary shopping-site image extraction should be done server-side because many sites restrict browser-side scraping/CORS.

## Roadmap
- [x] Camera
- [x] Individual items
- [x] Whole Outfit
- [x] Pose-aware placement
- [x] Product links
- [x] Capture
- [ ] Real garment segmentation
- [ ] Photorealistic AI VTON
- [ ] Multi-garment generation
- [ ] Product API integration
- [ ] Accounts/cloud saved outfits

## License
MIT