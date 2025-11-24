# Instead of relying on PIL's mask system:
img.paste(logo, position, logo)  # ← This caused the error

# We now do manual pixel blending:
for each pixel in logo:
    if pixel is not transparent:
        blend with background pixel using alpha value
