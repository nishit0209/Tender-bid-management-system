import os
import re

TEMPLATE_DIR = 'd:/Tender-Bid-management/templates'

# Mapping of old dark classes to new light and dark classes
# Format: 'old-class': ('light-class', 'dark-class')
CLASS_MAP = {
    'bg-slate-950': ('bg-slate-50', 'bg-slate-950'),
    'bg-slate-900': ('bg-white', 'bg-slate-900'),
    'bg-slate-800': ('bg-slate-50', 'bg-slate-800'),
    'bg-slate-700': ('bg-slate-100', 'bg-slate-700'),
    
    'text-slate-100': ('text-slate-900', 'text-slate-100'),
    'text-slate-200': ('text-slate-800', 'text-slate-200'),
    'text-slate-300': ('text-slate-700', 'text-slate-300'),
    'text-slate-400': ('text-slate-500', 'text-slate-400'),
    'text-slate-500': ('text-slate-600', 'text-slate-500'),
    
    'border-slate-800': ('border-slate-200', 'border-slate-800'),
    'border-slate-700': ('border-slate-300', 'border-slate-700'),
    'border-slate-600': ('border-slate-300', 'border-slate-600'),
    
    'divide-slate-800': ('divide-slate-200', 'divide-slate-800'),
    'ring-slate-800': ('ring-slate-200', 'ring-slate-800'),
    
    # Badges & Colors
    'bg-emerald-900/40': ('bg-emerald-100', 'bg-emerald-900/40'),
    'text-emerald-400': ('text-emerald-700', 'text-emerald-400'),
    
    'bg-amber-900/40': ('bg-amber-100', 'bg-amber-900/40'),
    'text-amber-400': ('text-amber-700', 'text-amber-400'),
    
    'bg-red-900/40': ('bg-red-100', 'bg-red-900/40'),
    'text-red-400': ('text-red-700', 'text-red-400'),
    'bg-red-900/20': ('bg-red-50', 'bg-red-900/20'),
    'bg-red-900/30': ('bg-red-100', 'bg-red-900/30'),
    'border-red-700/50': ('border-red-300', 'border-red-700/50'),
    'text-red-300': ('text-red-800', 'text-red-300'),

    'bg-indigo-900/40': ('bg-indigo-100', 'bg-indigo-900/40'),
    'text-indigo-400': ('text-indigo-700', 'text-indigo-400'),
    'text-indigo-300': ('text-indigo-700', 'text-indigo-300'),
    'text-indigo-200/80': ('text-indigo-800/80', 'text-indigo-200/80'),
    
    'bg-cyan-900/40': ('bg-cyan-100', 'bg-cyan-900/40'),
    'text-cyan-400': ('text-cyan-700', 'text-cyan-400'),

    'bg-purple-900/40': ('bg-purple-100', 'bg-purple-900/40'),
    'text-purple-400': ('text-purple-700', 'text-purple-400'),

    'bg-blue-900/60': ('bg-blue-100', 'bg-blue-900/60'),
    'text-blue-300': ('text-blue-700', 'text-blue-300'),
    'bg-blue-900/40': ('bg-blue-100', 'bg-blue-900/40'),
    'text-blue-400': ('text-blue-700', 'text-blue-400'),
    
    # Gradients for login page
    'from-slate-900': ('from-slate-100', 'from-slate-900'),
    'via-indigo-950': ('via-indigo-100', 'via-indigo-950'),
    'to-slate-900': ('to-slate-50', 'to-slate-900'),
}

def undo_previous_mess(content):
    """Reverts the naive find-and-replace from the previous buggy script versions."""
    # Undo text-white mess
    content = content.replace('text-slate-900 dark:text-white', 'text-white')
    
    # Undo CLASS_MAP messes
    for old_class, (light_class, dark_class) in CLASS_MAP.items():
        bad_string = f"{light_class} dark:{dark_class}"
        content = content.replace(bad_string, old_class)
    return content

def apply_correct_classes(content):
    """Applies the correct tailwind classes while preserving prefixes like hover:"""
    new_content = content
    
    def make_replacer(l_class, d_class):
        def replacer(match):
            prefix = match.group(1) or ''
            # If it already has dark:, skip it
            if 'dark:' in prefix:
                return match.group(0)
            return f"{prefix}{l_class} dark:{prefix}{d_class}"
        return replacer

    for old_class, (light_class, dark_class) in CLASS_MAP.items():
        # Match optional prefix (like hover:, md:, focus:) and the old class
        pattern = r'\b([a-z0-9:-]+:)?' + re.escape(old_class) + r'\b'
        new_content = re.sub(pattern, make_replacer(light_class, dark_class), new_content)

    # Special logic for text-white
    lines = new_content.split('\n')
    processed_lines = []
    colorful_bgs = ['bg-indigo-', 'bg-cyan-', 'bg-blue-', 'bg-emerald-', 'bg-red-', 'bg-green-', 'bg-amber-', 'bg-purple-', 'bg-gradient']
    
    for line in lines:
        if 'text-white' in line and not 'dark:text-white' in line:
            has_color_bg = any(bg in line for bg in colorful_bgs)
            if not has_color_bg:
                # Replace text-white with text-slate-900 dark:text-white, but preserve prefix
                line = re.sub(r'\b([a-z0-9:-]+:)?text-white\b', make_replacer('text-slate-900', 'text-white'), line)
        processed_lines.append(line)
        
    return '\n'.join(processed_lines)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Clean up the old bad replacements
    cleaned_content = undo_previous_mess(content)
    
    # Step 2: Apply the correct replacements
    final_content = apply_correct_classes(cleaned_content)

    if final_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        return True
    return False

def main():
    changed_files = 0
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if process_file(filepath):
                    print(f"Updated: {filepath}")
                    changed_files += 1
    
    print(f"Done! Changed {changed_files} files.")

if __name__ == '__main__':
    main()

