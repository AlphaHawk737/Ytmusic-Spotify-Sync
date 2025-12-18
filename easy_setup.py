"""
Easy setup helper - just tells you what to do
"""

print("\n" + "="*70)
print("YouTube Music Setup - Simple Method")
print("="*70 + "\n")

print("Run this command:")
print("\nytmusicapi browser --file headers_auth.json\n")

print("Then:")
print("  1. Chrome opens to music.youtube.com → Log in")
print("  2. Press F12 (Developer Tools)")
print("  3. Click 'Network' tab")
print("  4. Click any playlist/song (to generate requests)")
print("  5. Find a request to 'music.youtube.com'")
print("  6. Right-click → Copy → Copy as cURL")
print("  7. Paste into terminal")
print("  8. Press Ctrl+Z then Enter")
print("\nThis creates headers_auth.json (valid for months)")
print("="*70 + "\n")