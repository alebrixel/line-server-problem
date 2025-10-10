# generate_dummy.py
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_dummy.py <num_lines>")
        sys.exit(1)

    num_lines = int(sys.argv[1])
    output_file = "dummy.txt"

    buffer_size = 10000

    with open(output_file, 'w', encoding='ascii') as f:
        for start in range(0, num_lines, buffer_size):
            end = min(start + buffer_size, num_lines)
            lines = [f"Linha: {i}\n" for i in range(start, end)]
            f.writelines(lines)

    print(f"Generated {num_lines} lines in {output_file}")

if __name__ == "__main__":
    main()
