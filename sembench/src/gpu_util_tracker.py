from contextlib import contextmanager
import subprocess
import time
import csv
import tempfile
import os


@contextmanager
def track_gpu(device_index=0, interval_ms=50):
    """Track GPU utilization of any process using nvidia-smi daemon mode.

    nvidia-smi can sample at ~50ms intervals (much finer than NVML's
    nvmlDeviceGetUtilizationRates which uses a ~1s driver window).

    Yields a dict populated on exit with:
      - samples:      list of {timestamp_s, gpu_util, mem_util, power_w}
      - wall_time_s:  wall-clock duration
      - mean_gpu_util: average GPU utilization %
      - max_gpu_util:  peak GPU utilization %
      - mean_mem_util: average memory utilization %
    """
    results = {}
    tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    tmpfile.close()

    proc = subprocess.Popen(
        [
            "nvidia-smi",
            f"--id={device_index}",
            f"--loop-ms={interval_ms}",
            "--format=csv,noheader,nounits",
            "--query-gpu=timestamp,utilization.gpu,utilization.memory,power.draw",
        ],
        stdout=open(tmpfile.name, "w"),
        stderr=subprocess.DEVNULL,
    )

    # Give nvidia-smi a moment to start
    time.sleep(0.1)
    wall_start = time.perf_counter()

    try:
        yield results
    finally:
        wall_end = time.perf_counter()
        proc.terminate()
        proc.wait()

        samples = []
        with open(tmpfile.name, "r") as f:
            for row in csv.reader(f):
                if len(row) < 4:
                    continue
                try:
                    samples.append({
                        "timestamp": row[0].strip(),
                        "gpu_util": int(row[1].strip()),
                        "mem_util": int(row[2].strip()),
                        "power_w": float(row[3].strip()),
                    })
                except (ValueError, IndexError):
                    continue

        os.unlink(tmpfile.name)

        gpu_utils = [s["gpu_util"] for s in samples]
        mem_utils = [s["mem_util"] for s in samples]

        results.update({
            "samples": samples,
            "wall_time_s": wall_end - wall_start,
            "mean_gpu_util": sum(gpu_utils) / len(gpu_utils) if gpu_utils else 0,
            "max_gpu_util": max(gpu_utils) if gpu_utils else 0,
            "mean_mem_util": sum(mem_utils) / len(mem_utils) if mem_utils else 0,
            "num_samples": len(samples),
        })