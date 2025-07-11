def clear_placeholder(entry, placeholder, fg=None):
    if entry.get() == placeholder:
        entry.delete(0, 'end')
        if fg is not None:
            entry.config(fg=fg)
        else:
            entry.config(fg='white')

def restore_placeholder(entry, placeholder, fg=None):
    if not entry.get():
        entry.insert(0, placeholder)
        if fg is not None:
            entry.config(fg=fg)
        else:
            entry.config(fg='gray')

def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*'
    for ch in invalid_chars:
        name = name.replace(ch, '')
    return name.strip()
