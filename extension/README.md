# Extension

Firefox browser extension for Style Assistant.

## Structure

```
extension/
├── manifest.json           # Firefox extension manifest (Manifest V3)
├── src/                    # TypeScript source files
│   ├── background/         # Background service worker
│   ├── content/           # Content scripts
│   ├── popup/             # Extension popup
│   └── quiz/              # Style quiz page
├── dist/                   # Compiled JavaScript (gitignored)
├── content/styles.css      # Analysis box styles
├── popup/popup.html        # Popup HTML
├── quiz/quiz.html          # Quiz HTML
└── icons/                  # Extension icons

```

## Development Setup

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Watch mode for development
npm run watch

# Lint
npm run lint

# Format code
npm run format
```

## Loading in Firefox

1. Build the TypeScript: `npm run build`
2. Open Firefox
3. Navigate to `about:debugging#/runtime/this-firefox`
4. Click "Load Temporary Add-on"
5. Select `manifest.json` from this directory

## Architecture

- **Background Worker**: Handles API communication with backend
- **Content Scripts**: Detects product pages and injects analysis box
- **Popup**: Settings, quiz access, cost tracking display
- **Quiz**: Style profile questionnaire (opens in new tab)

## Browser API Usage

- `browser.storage.local` - Store settings and session data
- `browser.tabs` - Open quiz in new tab
- `browser.runtime` - Message passing between components
