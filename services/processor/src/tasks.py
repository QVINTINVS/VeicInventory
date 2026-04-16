import hashlib
import io
import json
import os
import subprocess

import boto3
import zstandard as zstd
from botocore.config import Config
from dotenv import load_dotenv

run_script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fortran", "run.sh")
)

env = os.environ.copy()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4"),
)


def upload_to_minio(file_bytes, bucket_name: str, object_key: str):
    fileobj = io.BytesIO(file_bytes)
    s3.upload_fileobj(fileobj, bucket_name, object_key)


def compress_file(path: str):
    with open(path, "rb") as f:
        data = f.read()

    cctx = zstd.ZstdCompressor(level=3)
    return cctx.compress(data)


def run_and_capture():
    completed = subprocess.run(
        ["/bin/bash", run_script_path],
        env=env,
        capture_output=True,
        text=True,
    )

    output = completed.stdout + completed.stderr
    return completed.returncode, output


def insert_round_wrfem_output(queue_item: dict):
    load_dotenv()

    file_00to12_path = os.getenv("WRFEM_OUTPUT_00TO12")
    file_12to24_path = os.getenv("WRFEM_OUTPUT_12TO24")

    if not file_00to12_path or not file_12to24_path:
        raise ValueError("Caminhos dos arquivos não configurados no .env")

    data_00to12_path = compress_file(file_00to12_path)
    data_12to24_path = compress_file(file_12to24_path)

    pk = queue_item.get("pk")
    panel_id = queue_item.get("fields", {}).get("panel")
    timestamp = queue_item.get("timestamp")

    base_string = f"queue_pk{pk}_panel{panel_id}_timestamp{timestamp}"
    round_id = hashlib.sha256(base_string.encode()).hexdigest()[:12]

    upload_to_minio(
        data_00to12_path, "wrfchemi-blobs", f"wrfchemi/round_{round_id}_00to12.zst"
    )
    upload_to_minio(
        data_12to24_path, "wrfchemi-blobs", f"wrfchemi/round_{round_id}_12to24.zst"
    )

    return round_id


def process_emission(emission_json: str):
    print("Job recebido!")

    data = json.loads(emission_json)

    print("Round recebido:")
    print(json.dumps(data, indent=4))

    print("Executando run.sh...")

    status, output = run_and_capture()

    print(output)

    if status:
        print("Erro no run.sh")

    insert_round_wrfem_output(data)
