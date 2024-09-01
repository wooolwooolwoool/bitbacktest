import subprocess
import argparse


def run_script(script_args):
    try:
        args = ['python3']
        args.extend(script_args)
        result = subprocess.run(args,
                                check=True,
                                text=True,
                                capture_output=True)
        print(f"Output of {script_args[0]}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running {script_args[0]}: {e.stderr}")


if __name__ == "__main__":
    tmp_file = "_tmp_lambda.py"
    parser = argparse.ArgumentParser(
        description=
        "Generate a CloudFormation template with an embedded Lambda function code."
    )
    parser.add_argument("-d",
                        "--directories",
                        nargs="+",
                        help="The directories to search for Python files.")
    parser.add_argument("-s",
                        "--strategy-class",
                        required=True,
                        help="Strategy Class Name.")
    parser.add_argument("-m",
                        "--market-class",
                        default="BitflyerMarket",
                        help="Market Class Name.")
    parser.add_argument("-o",
                        "--output-file",
                        default="CloudFormation.yaml",
                        help="Path to the output file.")
    parser.add_argument(
        "-a",
        "--additional_target_names",
        nargs="+",
        help="The names of the target functions and classes to include.")

    args = parser.parse_args()

    comb_args = [
        "./app/aws_build/build_lambda_src.py", "-s", args.strategy_class, "-m",
        args.market_class, "-o", tmp_file
    ]
    if args.directories is None:
        args.directories = []
    if not "src/" in args.directories:
        args.directories.append("src/")
    if args.directories is not None:
        comb_args.append("-d")
        comb_args.extend(args.directories)
    if args.additional_target_names is not None:
        comb_args.append("-a")
        comb_args.extend(args.additional_target_names)
    run_script(comb_args)

    CF_args = [
        "./app/aws_build/build_cloud_formation.py", "-p", tmp_file, "-o",
        args.output_file
    ]
    run_script(CF_args)
