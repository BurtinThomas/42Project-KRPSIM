import os

def read_file(file_name):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(project_root, file_name)
    with open(path, 'r') as f:
        return f.read()

def write_file(file_name, content):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    traces_dir = os.path.join(project_root, 'traces')
    os.makedirs(traces_dir, exist_ok=True)
    path = os.path.join(traces_dir, os.path.basename(file_name))
    with open(path, 'a') as f:
        f.write(content)