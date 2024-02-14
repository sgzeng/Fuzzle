import math
import os
import sys
import matplotlib.pyplot as plt
from PIL import Image
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
    red = [255, 0, 0, 255]
    black = [0, 0, 0, 255]
    rgba_matrix = [[black if cell == 4 else red for cell in row] for row in matrix]
    for i in range(size*size):
        y, x = 2*int(i/size)+1, 2*(i%size)+1
        if counters[i] > 0:
            # Calculate transparency based on coverage count
            alpha = int((counters[i] / max_counter) * 255)
            rgba_matrix[y][x] = [0, 255, 0, alpha]  # Green with calculated transparency
            matrix[y][x] = 3  # Mark as covered
        else:
            matrix[y][x] = 0  # Mark as uncovered
        # Note: Uncovered cells are already set to pure red, and walls to black
    # fix the edges
    green = [0, 255, 0, 255]
    for i in range(size*2+1):
        for j in range(size*2+1):
            if matrix[i][j] == 1:
                nodes = list()
                if i-1 > 0 and rgba_matrix[i-1][j][:3] == green[:3]:
                    nodes.append(rgba_matrix[i-1][j])
                if j-1 > 0 and rgba_matrix[i][j-1][:3] == green[:3]:
                    nodes.append(rgba_matrix[i][j-1])
                if i+1 < len(matrix) and rgba_matrix[i+1][j][:3] == green[:3]:
                    nodes.append(rgba_matrix[i+1][j])
                if j+1 < len(matrix[0]) and rgba_matrix[i][j+1][:3] == green[:3]:
                    nodes.append(rgba_matrix[i][j+1])
                if nodes: rgba_matrix[i][j] = min(nodes)
    return rgba_matrix

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
                    pixels[x*scale_factor + dx, y*scale_factor + dy] = tuple(grid[y][x])
    img.save(out_path)

def main(maze_txt, counter_file, out_path, size):
    matrix = get_matrix(maze_txt)
    rgba_matrix = visualize_coverage(matrix, counter_file, size)
    save_image(rgba_matrix, out_path)

if __name__ == '__main__':
    maze_txt = sys.argv[1]
    counter_file = sys.argv[2]
    out_dir = os.path.dirname(counter_file)
    size = int(math.sqrt(int(sys.argv[3])))
    i = 0
    while True:
        main(maze_txt, counter_file, f'{out_dir}/{i}.png', size)
        time.sleep(60)
        i += 1
