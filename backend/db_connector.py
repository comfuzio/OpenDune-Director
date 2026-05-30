import subprocess
import os

# Configuration for your specific Kubernetes setup
K8S_NAMESPACE = os.environ.get("DUNE_K8S_NAMESPACE", "default")
POSTGRES_SELECTOR = os.environ.get("POSTGRES_SELECTOR", "app=dune-postgres") # Adjust label to match your k3s deployment

def get_postgres_pod():
    """Dynamically finds the active Postgres pod name in the cluster."""
    cmd = [
        "kubectl", "get", "pods",
        "-n", K8S_NAMESPACE,
        "-l", POSTGRES_SELECTOR,
        "-o", "jsonpath={.items[0].metadata.name}"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to locate Postgres pod: {e.stderr}")

def run_psql(sql, timeout=60):
    """Executes a single SQL query via kubectl."""
    pod_name = get_postgres_pod()
    cmd = [
        "kubectl", "exec", "-n", K8S_NAMESPACE, pod_name, "--",
        "psql", "-U", "dune", "-d", "dune", "-v", "ON_ERROR_STOP=1", "-c", sql
    ]
    
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    
    return (
        "$ " + " ".join(cmd)
        + "\n\nSTDOUT:\n" + proc.stdout
        + "\nSTDERR:\n" + proc.stderr
        + f"\nExit code: {proc.returncode}"
    )

def run_psql_script(sql, timeout=180):
    """Passes a multi-line SQL script through stdin via kubectl."""
    pod_name = get_postgres_pod()
    # Notice the '-i' flag is crucial here for passing input through stdin
    cmd = [
        "kubectl", "exec", "-i", "-n", K8S_NAMESPACE, pod_name, "--",
        "psql", "-U", "dune", "-d", "dune", "-v", "ON_ERROR_STOP=1"
    ]
    
    proc = subprocess.run(
        cmd,
        input=sql,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

    return (
        "$ " + " ".join(cmd)
        + "\n\nSTDOUT:\n" + proc.stdout
        + "\nSTDERR:\n" + proc.stderr
        + f"\nExit code: {proc.returncode}"
    )
