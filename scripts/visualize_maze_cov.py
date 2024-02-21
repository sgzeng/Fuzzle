import math
import os
import shutil
import sys
import traceback
import matplotlib.pyplot as plt
from PIL import Image, ImageColor
import time

def scale_maze(maze_txt):
    wall, not_wall = '4', '1'
    with open(maze_txt, 'r+') as f:
        maze = f.read().replace('1', wall).replace('0', not_wall)
    return maze

def get_matrix(maze_txt):
    maze = scale_maze(maze_txt)
    rows = maze.split('\n')
    matrix = []
    for row in rows:
        matrix_row = []
        for c in row:
            matrix_row.append(int(c))
        if len(matrix_row) != 0:
            matrix.append(matrix_row)
    return matrix

def visualize_coverage(matrix, counter_file, size):
    with open(counter_file, 'r') as f:
        counters = [int(line.strip()) for line in f]
    max_counter = float(max(counters)) if counters else 1  # Avoid division by zero
    red = 'hsl(0, 100%, 50%)'
    black = 'hsl(0, 0%, 0%)'
    hsl_matrix = [[black if cell == 4 else red for cell in row] for row in matrix]
    for i in range(size*size):
        y, x = 2*int(i/size)+1, 2*(i%size)+1
        if counters[i] > 0:
            # Green with calculated brightness based on coverage count
            brightness = int(100 - 90 * (counters[i] / max_counter))
            hsl_color = f'hsl(120, 100%, {brightness}%)'
            hsl_matrix[y][x] = hsl_color
            matrix[y][x] = 3  # Mark as covered
        else:
            matrix[y][x] = 0  # Mark as uncovered
        # Note: Uncovered cells are already set to pure red, and walls to black
    # fix the edges
    green_parttern = 'hsl(120, 100%,'
    for i in range(size*2+1):
        for j in range(size*2+1):
            if matrix[i][j] == 1:
                nodes = list()
                if i-1 > 0 and green_parttern in hsl_matrix[i-1][j]:
                    nodes.append(hsl_matrix[i-1][j].split(',')[2].split('%')[0].strip())
                if j-1 > 0 and green_parttern in hsl_matrix[i][j-1]:
                    nodes.append(hsl_matrix[i][j-1].split(',')[2].split('%')[0].strip())
                if i+1 < len(matrix) and green_parttern in hsl_matrix[i+1][j]:
                    nodes.append(hsl_matrix[i+1][j].split(',')[2].split('%')[0].strip())
                if j+1 < len(matrix[0]) and green_parttern in hsl_matrix[i][j+1]:
                    nodes.append(hsl_matrix[i][j+1].split(',')[2].split('%')[0].strip())
                if nodes:
                    hsl_color = f'hsl(120, 100%, {min([int(n) for n in nodes])}%)'
                    hsl_matrix[i][j] = hsl_color
    return hsl_matrix

def save_image(grid, out_path, scale_factor=10, dpi=(200, 200)):
    original_height = len(grid)
    original_width = len(grid[0]) if original_height else 0
    new_width = original_width * scale_factor
    new_height = original_height * scale_factor
    img = Image.new('RGBA', (new_width, new_height))
    pixels = img.load()
    for y in range(original_height):
        for x in range(original_width):
            for dy in range(scale_factor):
                for dx in range(scale_factor):
                    rgb_color = ImageColor.getcolor(grid[y][x], 'RGB')
                    pixels[x*scale_factor + dx, y*scale_factor + dy] = tuple(rgb_color)
    img.save(out_path)

def main(maze_txt, counter_file, out_path, size):
    matrix = get_matrix(maze_txt)
    hsl_matrix = visualize_coverage(matrix, counter_file, size)
    save_image(hsl_matrix, out_path)

if __name__ == '__main__':
    maze_txt = sys.argv[1]
    counter_file = sys.argv[2]
    out_dir = os.path.dirname(counter_file)
    size = int(math.sqrt(int(sys.argv[3])))

    if len(sys.argv) == 5:
        out_file = sys.argv[4]
        main(maze_txt, counter_file, out_file, size)
        sys.exit(0)
    
    start_time = time.time()
    while True:
        try:
            current_time = time.time()
            elapsed_time = int(current_time - start_time)
            shutil.copy(counter_file, f'{out_dir}/{elapsed_time}.txt')
            main(maze_txt, counter_file, f'{out_dir}/{elapsed_time}.png', size)
        except Exception as e:
            with open(f'{out_dir}/error_{elapsed_time}.txt', 'w') as f:
                traceback.print_exc(file=f) 
                f.write(str(e))
        time.sleep(59)
