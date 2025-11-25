# Threads of Grace Website

A contemplative website showcasing Pat Horn's spiritual meditations on the Sunday lectionary readings.

## Website Structure

```
threads-of-grace-website/
├── index.html                  # Homepage
├── chronological.html          # All 20 meditations by date
├── styles.css                  # Main stylesheet
├── listing.css                 # Styles for listing pages
├── meditation.css              # Styles for individual meditations
├── script.js                   # JavaScript for interactions
├── meditations-data.json       # Meditation metadata
└── meditations/                # Individual meditation pages
    ├── 2008-11-02.html
    ├── 2009-08-23.html
    └── ... (20 total)
```

## Features

✨ **Beautiful, Contemplative Design**
- Elegant typography (Cormorant Garamond + Crimson Pro)
- Warm, cream color palette
- Subtle texture overlay
- Smooth animations and transitions
- Fully responsive (mobile-friendly)

📖 **Content**
- 20 carefully selected meditations (2008-2023)
- All liturgical seasons represented
- All three lectionary years (A, B, C)
- Clean, readable text formatting
- Navigation between meditations

🎨 **Design Choices**
- Drop caps on first paragraphs
- Generous spacing for contemplation
- Justified text for meditation content
- Hover effects for interactive elements
- Fade-in animations on scroll

## Deployment to Netlify

### Option 1: Drag and Drop (Easiest)

1. Go to [Netlify](https://www.netlify.com/)
2. Sign up or log in
3. Click "Add new site" → "Deploy manually"
4. Drag the entire `threads-of-grace-website` folder to the upload area
5. Wait for deployment (< 1 minute)
6. Your site is live! Netlify will give you a URL like `random-name.netlify.app`

### Option 2: Netlify CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Navigate to website folder
cd threads-of-grace-website

# Deploy
netlify deploy

# Follow prompts, then:
netlify deploy --prod
```

### Option 3: Git + Netlify (Best for updates)

1. Create a Git repository
2. Push the website folder to GitHub
3. Connect Netlify to your GitHub repo
4. Netlify will auto-deploy on every commit

## Custom Domain

Once deployed, you can add a custom domain in Netlify:
1. Go to Site settings → Domain management
2. Add your custom domain
3. Follow DNS configuration instructions
4. SSL certificate is automatic!

## Future Enhancements (Phase 2)

- [ ] Add "By Season" page
- [ ] Add "By Year" page
- [ ] Add search functionality
- [ ] Add remaining ~629 meditations
- [ ] Add scripture cross-reference
- [ ] Consider audio readings
- [ ] Add print/PDF options

## Technologies Used

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with variables
- **JavaScript** - Smooth interactions
- **Google Fonts** - Typography (Cormorant Garamond, Crimson Pro)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Android)

## Credits

- **Author**: Pat Horn
- **Website Development**: Created by her family
- **Design**: Contemplative, elegant aesthetic honoring Pat's spiritual legacy

## License

© 2007–2025 Pat Horn. All rights reserved.

The meditations are the copyrighted work of Pat Horn. This website is created to preserve and share her spiritual legacy.

---

## Local Development

To test locally:

1. Open `index.html` in a web browser
2. Or use a local server:
   ```bash
   # Python
   python -m http.server 8000
   
   # Node.js
   npx serve
   ```
3. Navigate to `http://localhost:8000`

## Notes

- All text has been cleaned (removed photo credits, formatting marks)
- Meditation content is in `/meditations_cleaned/` if you need to edit
- Filenames follow pattern: `YYYY-MM-DD.html`
- All links are relative (works locally and deployed)
- No build process required - static HTML files
