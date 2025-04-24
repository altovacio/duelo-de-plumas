# Duelo de Plumas - Social Media Assets Instructions

## What's Been Set Up

I've prepared your website with:

1. An `images` folder in the `app/static` directory to store all image assets
2. Metadata tags in the base template for social media sharing (Open Graph and Twitter)
3. Favicon links in different sizes for various devices

## Assets You Need to Create

### 1. Social Sharing Image

**File name:** `duelo-plumas-share.jpg`  
**Recommended size:** 1200 × 630 pixels  
**Location:** `app/static/images/`

**Design suggestions:**
- Feature your "Duelo de Plumas" logo prominently
- Use a clean background with a literary theme (books, pens, quills, etc.)
- Include a short tagline: "Plataforma de Concursos Literarios"
- Use your brand colors, but ensure good contrast for readability
- Keep the design relatively simple - it will appear as a small thumbnail in WhatsApp

### 2. Favicon Files

Create these favicon files:
- `favicon-16x16.png` (16×16 pixels)
- `favicon-32x32.png` (32×32 pixels)
- `apple-touch-icon.png` (180×180 pixels)

**Location:** `app/static/images/`

**Design suggestions:**
- Create a simple, recognizable icon representing "Duelo de Plumas"
- Consider using a quill pen icon or stylized "DP" initials
- Ensure it's recognizable even at the smallest size (16×16)
- Use solid colors rather than complex gradients

## How to Generate These Assets

### Option 1: Use a Graphic Design Tool

If you have design skills:
1. Use Adobe Photoshop, Illustrator, or free alternatives like GIMP, Inkscape, or Canva
2. Create the designs according to the specifications above
3. Export them in the correct formats and sizes
4. Upload them to the `app/static/images/` directory

### Option 2: Use an Online Generator

For the favicon:
1. Use [Favicon.io](https://favicon.io/) or [RealFaviconGenerator](https://realfavicongenerator.net/)
2. Upload a high-quality image or create one from text
3. Download the generated package
4. Extract and move the required files to your `app/static/images/` directory

For the social sharing image:
1. Use [Canva](https://www.canva.com/) with a social media template
2. Design your image (1200×630px)
3. Download as JPG
4. Upload to your `app/static/images/` directory

### Option 3: Hire a Designer

If you want professional results:
1. Hire a designer on platforms like Fiverr or Upwork
2. Provide them with these specifications and your brand guidelines
3. Ask them to deliver all required files in the correct formats

## WhatsApp Sharing Description

When sharing your website link on WhatsApp, the following description will appear based on the metadata I've added:

**Title:** "Duelo de Plumas - Plataforma de Concursos Literarios"

**Description:** "Participa en concursos literarios, comparte tus obras y descubre talentos emergentes en nuestra comunidad de escritores."

This text is set in the Open Graph metadata and can be updated in the base.html file if you'd like to change it.

## Verifying Your Implementation

Once you've created and uploaded all assets:
1. Clear your browser cache
2. Visit your website and check if the favicon appears in the browser tab
3. Use the [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) to preview how your link will appear when shared
4. Test sharing a link to your site on WhatsApp to ensure the image and description appear correctly

If something doesn't look right, check that:
- Files are in the correct location with the exact names specified in the HTML
- Image dimensions match the recommendations
- Your web server is correctly serving the static files 