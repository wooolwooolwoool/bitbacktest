import argparse
import re


def extract_static_keys_from_file(file_path):
  # ファイルの内容を読み込みます
  with open(file_path, 'r') as file:
    script = file.read()

  # 正規表現パターンを定義します
  pattern = r'self\.static\["([^"]+)"\]'

  # パターンにマッチする全ての部分を検索します
  matches = re.findall(pattern, script)

  return matches


def create_cloudformation_template(lambda_code_path, output_file,
                                   lambda_function_name, lambda_role_arn,
                                   environment_variables):
  with open(lambda_code_path, 'r', encoding='utf-8') as f:
    lambda_codes = []
    for line in f.readlines():
      lambda_codes.append("          " + line)
    lambda_code = "".join(lambda_codes)

  env_variables_yaml = "\n".join(
      [f"          {env}: 0" for env in environment_variables])

  template_base_path = "./app/_template.yaml"
  with open(template_base_path, 'r', encoding='utf-8') as f:
    template_base = f.read()

  template = template_base.format(lambda_function_name=lambda_function_name,
                                  lambda_role_arn=lambda_role_arn,
                                  lambda_code=lambda_code,
                                  env_variables=env_variables_yaml)

  with open(output_file, 'w', encoding='utf-8') as f:
    f.write(template.strip())
  print(f"CloudFormation template has been written to {output_file}")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Build all")
  parser.add_argument("-p",
                      "--lambda_code_path",
                      type=str,
                      required=True,
                      help="Path to lambda code")
  parser.add_argument("-o",
                      "--output_file",
                      type=str,
                      required=True,
                      help="Path to output file")
  parser.add_argument("--lambda_function_name",
                      type=str,
                      default="Myfunction",
                      help="Name of Lambda function")
  parser.add_argument("--lambda_role_arn",
                      type=str,
                      default="arn:aws:iam::xxxxx",
                      help="AWS IAM role ARN for Lambda function")
  args = parser.parse_args()

  envs = extract_static_keys_from_file(args.lambda_code_path)
  envs.extend(
      ["API_KEY", "API_SECRET", "TABLE_NAME", "PARAMS_KEY", "TRADE_ENABLE"])

  create_cloudformation_template(
      lambda_code_path=args.lambda_code_path,
      output_file=args.output_file,
      lambda_function_name=args.lambda_function_name,
      lambda_role_arn=args.lambda_role_arn,
      environment_variables=envs)
