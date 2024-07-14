import os
import re
import argparse


def find_python_files(directories):
    """Recursively find all Python files in the given directories."""
    python_files = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
    return python_files


def extract_class_hierarchy(file_path, target_classes):
    """Extract class hierarchy for target classes from a Python file."""
    class_hierarchy = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        match = re.match(r'^\s*class\s+(\w+)\s*\(([\w\s,]*)\)\s*:', line)
        if match:
            class_name, base_classes = match.groups()
            base_classes = [
                base_class.strip() for base_class in base_classes.split(',')
                if base_class.strip()
            ]
            if class_name in target_classes:
                class_hierarchy[class_name] = base_classes
    return class_hierarchy


def get_all_superclasses(class_hierarchy, target_classes):
    """Get all superclasses for the target classes."""
    superclasses = set()

    def add_superclasses(class_name):
        if class_name in class_hierarchy:
            for base_class in class_hierarchy[class_name]:
                if base_class not in target_classes and base_class not in superclasses:
                    superclasses.add(base_class)
                    add_superclasses(base_class)

    for class_name in target_classes:
        add_superclasses(class_name)

    return superclasses


def extract_imports_and_definitions(file_path, target_names, logger):
    """Extract relevant import statements and definitions from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    imports = []
    definitions = []
    inside_class = False
    current_indent_level = 0
    current_class_lines = []

    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith(
                "from "):
            imports.append(line)
        elif re.match(r'^\s*class\s+(\w+)\s*[\(:]', line):
            class_name = re.findall(r'^\s*class\s+(\w+)\s*[\(:]', line)[0]
            if class_name in target_names:
                inside_class = True
                current_indent_level = len(line) - len(line.lstrip())
                print(current_indent_level)
                current_class_lines.append(line)
                logger(f"Found class: {class_name}")
                target_names.remove(class_name)

            elif inside_class and len(line) - len(
                    line.lstrip()) <= current_indent_level:
                definitions.extend(current_class_lines)
                inside_class = False
                current_class_lines = []
                logger(f"End class: {class_name}")
        elif not inside_class and re.match(r'^\s*def\s+(\w+)\s*\(', line):
            func_name = re.findall(r'^\s*def\s+(\w+)\s*\(', line)[0]
            if func_name in target_names:
                definitions.append(line)
                logger(f"Found function: {func_name}")
        elif inside_class:
            current_class_lines.append(line)

    if inside_class:
        definitions.extend(current_class_lines)

    return imports, definitions


def combine_files(directory, output_file, target_names):
    """Combine relevant import statements and definitions from all Python files in the directory."""
    all_imports = set()
    all_definitions = []
    class_hierarchy = {}

    def logger(message):
        print(message)

    python_files = find_python_files(directory)

    # Step 1: Extract class hierarchy
    for file_path in python_files:
        class_hierarchy.update(extract_class_hierarchy(file_path,
                                                       target_names))

    # Step 2: Get all superclasses
    superclasses = get_all_superclasses(class_hierarchy, target_names)
    target_names.update(superclasses)

    # Step 3: Extract relevant imports and definitions
    for file_path in python_files:
        imports, definitions = extract_imports_and_definitions(
            file_path, target_names, logger)
        if definitions != []:
            all_imports.update(imports)
            all_definitions.extend(definitions)

    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write("# Combined Python file\n")
        out_file.write("# Import statements\n")
        for imp in sorted(all_imports):
            out_file.write(imp)
        out_file.write("\n# Function and Class definitions\n")
        for definition in all_definitions:
            out_file.write(definition)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        "Combine specific functions and classes from Python files into one file.\n ex) python build.py -d /path/to/dir1 /path/to/dir2 -o combined_output.py MyFunction MyClass"
    )
    parser.add_argument("-d",
                        "--directories",
                        nargs="+",
                        required=True,
                        help="The directories to search for Python files.")
    parser.add_argument("-o",
                        "--output-file",
                        required=True,
                        help="The path of the output file.")
    parser.add_argument(
        "target_names",
        nargs="+",
        help="The names of the target functions and classes to include.")

    args = parser.parse_args()

    combine_files(args.directories, args.output_file, set(args.target_names))
