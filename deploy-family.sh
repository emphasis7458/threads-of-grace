#!/bin/bash
# deploy-family.sh — Encrypt family pages and deploy to Netlify
#
# Usage:
#   STATICRYPT_PASSWORD="your-password" ./deploy-family.sh
#
# Or set the password in the environment first:
#   export STATICRYPT_PASSWORD="your-password"
#   ./deploy-family.sh

set -e

FAMILY_FILES="family/index.html family/stories-mom-told.html family/stories-mom-wrote.html family/family-history.html family/family-tree.html family/memorial-video.html"

if [ -z "$STATICRYPT_PASSWORD" ]; then
    echo "Error: STATICRYPT_PASSWORD environment variable is not set."
    echo "Usage: STATICRYPT_PASSWORD=your-password ./deploy-family.sh"
    exit 1
fi

# Strip surrounding quotes if present (some shells pass them as part of the value)
STATICRYPT_PASSWORD="${STATICRYPT_PASSWORD#\'}"
STATICRYPT_PASSWORD="${STATICRYPT_PASSWORD%\'}"
STATICRYPT_PASSWORD="${STATICRYPT_PASSWORD#\"}"
STATICRYPT_PASSWORD="${STATICRYPT_PASSWORD%\"}"

echo "Encrypting family pages..."
echo "Password length: ${#STATICRYPT_PASSWORD} characters"
npx staticrypt $FAMILY_FILES -p "$STATICRYPT_PASSWORD" --remember 30 -t family/password-template.html --template-title 'Horn Family' --template-button 'Enter' --template-instructions 'This area is for family members.' --template-error 'Incorrect password. Please try again.' --template-placeholder 'Family password' -d family --short

echo ""
echo "Verifying encryption..."
if npx staticrypt --decrypt family/index.html -p "$STATICRYPT_PASSWORD" -d /tmp/staticrypt-verify > /dev/null 2>&1; then
    echo "Verification passed — password decrypts correctly."
    rm -rf /tmp/staticrypt-verify
else
    echo "ERROR: Verification FAILED — encrypted file cannot be decrypted with the given password!"
    echo "Aborting deploy."
    exit 1
fi

echo ""
echo "Deploying to Netlify..."
netlify deploy --prod --dir=.

echo ""
echo "Restoring source HTML files..."
# Try git checkout first (works if files are committed), fall back to decrypt
if git checkout -- $FAMILY_FILES 2>/dev/null; then
    echo "Restored from git."
else
    npx staticrypt --decrypt $FAMILY_FILES -p "$STATICRYPT_PASSWORD" -d family
    echo "Restored via decryption."
fi

echo ""
echo "Done! Family pages are encrypted and deployed."
