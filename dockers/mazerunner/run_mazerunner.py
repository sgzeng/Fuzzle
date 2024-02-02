import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


with open("launch_exp.ipynb") as f:
    nb = nbformat.read(f, as_version=4)

# 创建一个执行器，用于运行cells
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

# 选择要运行的cells的编号
cells_to_run = [2, 4, 6]

# 创建一个新的notebook对象，只包含选定的cells
new_nb = nbformat.v4.new_notebook()
new_nb.cells = [nb.cells[i] for i in cells_to_run]

# 执行这些cells
ep.preprocess(new_nb, {'metadata': {'path': '运行cells的路径'}})

# 保存新的notebook
with open("处理后的notebook文件路径.ipynb", 'w', encoding='utf-8') as f:
    nbformat.write(new_nb, f)
