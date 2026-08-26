# RoboLab 2.1.0 — Public Free Release

RoboLab is a FastAPI-based robotics engineering platform by SynapseX Robotics & Technologies.

## Included free modules
- Engineering planner and budget estimate
- Component catalog
- Availability API with optional live supplier-feed adapters
- Automatic Arduino/ESP32 firmware starter generation
- Automatic wiring/circuit SVG generation
- Lightweight 2D kinematic robotics simulation
- OpenSCAD CAD starter generation
- Optional Google OAuth

## Live component availability
The application supports live supplier adapters through the `SUPPLIER_FEEDS` environment variable. Example:

`SUPPLIER_FEEDS={"supplier-name":"https://your-domain.example/inventory.json"}`

The feed should return JSON with an `items` field. With no feed configured, RoboLab reports catalog availability and does **not** claim real retailer stock.

## Security
Never commit `.env`, Google client secrets, API keys, or production session secrets. Use environment variables. Google Client Secret is backend-only.

## Run
```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `/` for the web app and `/docs` for the API documentation.

## Important engineering note
Generated firmware, wiring, CAD, and simulation are starter engineering tools. Verify electrical limits, pin mappings, current requirements, mechanical clearances, and firmware behavior before building hardware.
