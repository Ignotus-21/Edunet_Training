# Edunet_Training

Modernized training repository featuring **Gastronomix AI**, a Streamlit application that helps users recognize ingredients, manage a pantry, and generate low-waste recipe ideas.

## Highlights
- Modern Streamlit UI with a cleaner layout and app theming
- AI-powered food image analysis using a single Google API key
- Recipe generation with graceful fallback behavior when AI is unavailable
- Pantry tracking, storage guidance, and low-waste suggestions
- Updated project structure for the Streamlit app assets and configuration

## Streamlit application
Location: `Code/streamlit_application`

### Features
- Upload or capture food images for ingredient recognition
- Build a pantry board from detected or manual ingredients
- Generate recipe ideas based on cuisine, meal goal, and time limit
- View storage advice and waste-reduction tips for pantry items
- Run without crashing even when API configuration is missing

### Updated structure
```text
Code/streamlit_application/
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml
├── assets/
│   ├── branding/
│   │   ├── logo_black.jpg
│   │   └── logo_white.jpg
│   └── media/
│       ├── Gastronomix AI.mp4
│       └── Presentation.pptx
├── requirements.txt
└── streamlit_app.py
```

## Getting started
1. Create and activate a Python environment.
2. Install the app dependencies:
   ```bash
   pip install -r Code/streamlit_application/requirements.txt
   ```
3. Add your Google AI Studio key to `Code/streamlit_application/.streamlit/secrets.toml`.
4. Start the app:
   ```bash
   streamlit run Code/streamlit_application/streamlit_app.py
   ```

## Repository notes
- `YOLO_V5_DATASET/` contains the dataset assets used elsewhere in the training repository.
- `Code/resource_links.txt` stores related project references.
- The root `README.md` now focuses on the runnable Streamlit experience.
