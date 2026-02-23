import re
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the nav block
    nav_match = re.search(r'(<nav[^>]*>)(.*?)(</nav>)', content, re.DOTALL)
    if not nav_match:
        return

    nav_open = nav_match.group(1)
    nav_inner = nav_match.group(2)
    nav_close = nav_match.group(3)

    # Extract the hamburger button
    hamburger_pattern = r'(\s*<button class="hamburger".*?</button>\n+)'
    hamburger_match = re.search(hamburger_pattern, nav_inner, re.DOTALL)
    
    if not hamburger_match:
        return
        
    hamburger_html = hamburger_match.group(1)
    
    # Remove hamburger from its current position
    nav_inner_no_hamburger = nav_inner.replace(hamburger_html, '')
    
    # Insert hamburger before <div class="nav-right">, or if not present, before the closing </nav>
    if '<div class="nav-right">' in nav_inner_no_hamburger:
        new_nav_inner = nav_inner_no_hamburger.replace('<div class="nav-right">', hamburger_html + '    <div class="nav-right">')
    else:
        # Should not happen since we added nav-right everywhere, but just in case
        new_nav_inner = hamburger_html + nav_inner_no_hamburger
        
    new_content = content[:nav_match.start()] + nav_open + new_nav_inner + nav_close + content[nav_match.end():]
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Fixed {filepath}")

for f in glob.glob('/home/debian/fullsteamaheadhome/*.html'):
    fix_file(f)
