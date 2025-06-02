import subprocess
import sys
import os
import venv
import atexit
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from jupyter_client.manager import KernelManager
    from jupyter_client.blocking.client import BlockingKernelClient
    from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
except ImportError:
    print(
        "Error: jupyter_client is not installed. Please install it: pip install jupyter_client"
    )
    sys.exit(1)


class Runtime:
    """
    Manages a Python virtual environment and a Jupyter kernel for isolated code execution.
    """

    def __init__(self, runtime_env_name: str = ".venv_llm"):
        """
        Initializes the runtime environment.

        Args:
            runtime_env_name (str): The name of the directory for the virtual environment.
                                    This will be created in the project root (parent of 'execution' dir).
                                    If an absolute path is provided, it will be used directly.
        """
        _env_path = Path(runtime_env_name)
        # Assume runtime_env_name is a directory name for the project root
        # Project root is parent of 'execution' directory where this file typically lives
        project_root = Path(__file__).resolve().parent.parent
        self.run_env_path: Path = (project_root / runtime_env_name).resolve()

        self.kernel_manager: Optional[KernelManager] = None
        self.kernel_client: Optional[BlockingKernelClient] = None
        self.executed_cells: List[Dict[str, Any]] = []

        # Generate a unique kernel spec name based on the environment path
        safe_env_name = "".join(
            c if c.isalnum() else "_" for c in self.run_env_path.name
        )
        self.kernel_spec_name = f"llm_runtime_kernel_{safe_env_name}"

        self._setup_virtual_env()
        self._start_kernel()
        atexit.register(self.shutdown_kernel)  # Ensure cleanup on exit

    def _get_venv_executable(self, executable_name: str) -> str:
        """Gets the path to an executable (e.g., python, pip) in the venv."""
        if sys.platform == "win32":
            return str(self.run_env_path / "Scripts" / f"{executable_name}.exe")
        return str(self.run_env_path / "bin" / executable_name)

    def _setup_virtual_env(self):
        """Creates the virtual environment and installs necessary packages."""
        if (self.run_env_path / "pyvenv.cfg").exists():
            return
        print(f"Creating virtual environment in {self.run_env_path}...")
        venv.create(self.run_env_path, with_pip=True, system_site_packages=False)
        print(f"Virtual environment created.")

        venv_pip_path = self._get_venv_executable("pip")
        venv_python_path = self._get_venv_executable("python")

        print(
            f"Installing/updating jupyter_client and ipykernel in {self.run_env_path}..."
        )
        try:
            subprocess.check_call(
                [venv_pip_path, "install", "--upgrade", "jupyter_client", "ipykernel"],
                timeout=300,
            )
            print("jupyter_client and ipykernel installed/updated successfully.")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Error installing packages in venv: {e}")
            raise RuntimeError(
                f"Failed to install jupyter_client/ipykernel in {self.run_env_path}"
            ) from e

        # Install a kernel spec for this virtual environment's Python
        ksm = KernelSpecManager()
        try:
            ksm.get_kernel_spec(self.kernel_spec_name)
            print(f"Kernel spec '{self.kernel_spec_name}' already exists.")
        except NoSuchKernel:
            print(
                f"Installing kernel spec '{self.kernel_spec_name}' for the virtual environment..."
            )
            display_name = f"LLM Runtime Env ({self.run_env_path.name})"
            install_spec_cmd = [
                venv_python_path,
                "-m",
                "ipykernel",
                "install",
                "--user",  # Installs for the current user, making it findable by KernelManager
                f"--name={self.kernel_spec_name}",
                f"--display-name={display_name}",
            ]
            try:
                subprocess.check_call(install_spec_cmd, timeout=60)
                print(f"Kernel spec '{self.kernel_spec_name}' installed successfully.")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(
                    f"Warning: Error installing kernel spec '{self.kernel_spec_name}': {e}. Will try to launch kernel directly."
                )

    def _start_kernel(self):
        """Starts the Jupyter kernel and connects the client."""
        print(
            f"Starting Jupyter kernel using spec '{self.kernel_spec_name}' or direct command..."
        )
        try:
            # Attempt to use the installed kernel spec
            self.kernel_manager = KernelManager(kernel_name=self.kernel_spec_name)
        except NoSuchKernel:
            print(
                f"Kernel spec '{self.kernel_spec_name}' not found. Falling back to direct kernel command."
            )
            venv_python_path = self._get_venv_executable("python")
            kernel_cmd = [
                venv_python_path,
                "-m",
                "ipykernel_launcher",
                "-f",
                "{connection_file}",  # Placeholder filled by KernelManager
            ]
            self.kernel_manager = KernelManager(
                kernel_name="python3", kernel_cmd=kernel_cmd
            )
        except Exception as e:
            print(
                f"Failed to initialize KernelManager with spec '{self.kernel_spec_name}': {e}. Trying direct command."
            )
            venv_python_path = self._get_venv_executable("python")
            kernel_cmd = [
                venv_python_path,
                "-m",
                "ipykernel_launcher",
                "-f",
                "{connection_file}",
            ]
            self.kernel_manager = KernelManager(
                kernel_name="python3", kernel_cmd=kernel_cmd
            )

        if not self.kernel_manager:
            raise RuntimeError("Failed to initialize KernelManager.")

        self.kernel_manager.start_kernel()
        print(f"Kernel started. Connection file: {self.kernel_manager.connection_file}")

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        try:
            self.kernel_client.wait_for_ready(timeout=60)
            print("Kernel client connected and kernel is ready.")
        except RuntimeError as e:
            print(f"Timeout or error waiting for kernel to be ready: {e}")
            self.shutdown_kernel()
            raise RuntimeError(
                "Failed to connect to kernel or kernel not ready."
            ) from e

    def execute_code(self, code_string: str) -> List[Dict[str, Any]]:
        """
        Executes a string of Python code in the Jupyter kernel.
        This call is blocking and waits for execution to complete.

        Args:
            code_string (str): The Python code to execute.

        Returns:
            List[Dict[str, Any]]: A list of output messages from the kernel.
        """
        if not self.kernel_client or not self.kernel_client.is_alive():
            print("Kernel is not running or client not connected.")
            raise RuntimeError("Kernel not available for execution.")

        print(
            f"Executing code:\n{code_string[:200]}{'...' if len(code_string) > 200 else ''}"
        )
        msg_id = self.kernel_client.execute(
            code_string, store_history=True, silent=False
        )

        outputs = []

        # Loop to gather all outputs for this execution request
        # Timeout for get_iopub_msg should be reasonably short to remain responsive,
        # but long enough to not spam CPU if kernel is slow.
        # A total execution timeout might be needed for very long tasks.
        while True:
            try:
                io_msg = self.kernel_client.get_iopub_msg(timeout=10)  # seconds
            except Exception:  # Typically queue.Empty from timeout
                if not self.kernel_client.is_alive():
                    print("Kernel died during execution or while fetching output.")
                    outputs.append(
                        {
                            "type": "error",
                            "ename": "KernelDiedError",
                            "evalue": "Kernel died",
                            "traceback": [],
                        }
                    )
                    break
                # If it's just a timeout, continue waiting for the 'idle' status
                continue

            if io_msg["parent_header"].get("msg_id") != msg_id:
                # Not a message related to our execution request
                continue

            msg_type = io_msg["header"]["msg_type"]
            content = io_msg["content"]

            if msg_type == "status":
                if content["execution_state"] == "idle":
                    break  # Execution is complete for this cell
            elif msg_type == "stream":
                outputs.append(
                    {"type": "stream", "name": content["name"], "text": content["text"]}
                )
            elif msg_type == "display_data":
                outputs.append(
                    {
                        "type": "display_data",
                        "data": content["data"],
                        "metadata": content.get("metadata", {}),
                    }
                )
            elif msg_type == "execute_result":  # Explicit result of an expression
                outputs.append(
                    {
                        "type": "execute_result",
                        "data": content["data"],
                        "metadata": content.get("metadata", {}),
                    }
                )
            elif msg_type == "error":
                traceback_text = "\n".join(content.get("traceback", []))
                outputs.append(
                    {
                        "type": "error",
                        "ename": content["ename"],
                        "evalue": content["evalue"],
                        "traceback": traceback_text,
                    }
                )
            # Other messages like 'execute_input', 'clear_output' could be handled if needed.

        self.executed_cells.append({"code": code_string, "outputs": outputs})
        # print(f"Execution finished. Outputs: {outputs}") # Can be verbose
        return outputs

    def get_executed_cells(self) -> List[Dict[str, Any]]:
        """Returns a list of all executed code cells and their outputs."""
        return self.executed_cells

    def shutdown_kernel(self):
        """Shuts down the Jupyter kernel and cleans up resources."""
        print("Attempting to shut down Jupyter kernel...")
        if self.kernel_client:
            if self.kernel_client.channels_running:
                try:
                    self.kernel_client.stop_channels()
                except Exception as e:
                    print(f"Error stopping kernel client channels: {e}")
            self.kernel_client = None

        if self.kernel_manager:
            if self.kernel_manager.has_kernel and self.kernel_manager.is_alive():
                try:
                    self.kernel_manager.shutdown_kernel(
                        now=True
                    )  # now=True for immediate shutdown
                except Exception as e:
                    print(f"Error shutting down kernel manager: {e}")
            self.kernel_manager = None
        print("Kernel shutdown process complete.")


if __name__ == "__main__":
    print("Starting Runtime demo...")
    # Example usage:
    # Create a unique directory for this demo's environment to avoid conflicts
    # This will be created in the project root (e.g., llm-auto-api-integration/.llm_runtime_demo_env)
    demo_env_name = ".llm_runtime_demo_env"
    try:
        runtime = Runtime(runtime_env_name=demo_env_name)

        print("\nExecuting first cell...")
        outputs1 = runtime.execute_code(
            "print('Hello from the kernel!')\na = 10\nb = 20\na + b"
        )
        print("Outputs from cell 1:")
        for out in outputs1:
            if out["type"] == "stream":
                print(f"  Stream ({out['name']}): {out['text'].strip()}")
            elif out["type"] == "execute_result":
                print(
                    f"  Result: {out['data'].get('text/plain', 'No plain text output')}"
                )
            elif out["type"] == "error":
                print(f"  Error: {out['ename']}: {out['evalue']}\n{out['traceback']}")

        print("\nExecuting second cell (with an error)...")
        outputs2 = runtime.execute_code("print('This is another cell.')\n1/0")
        print("Outputs from cell 2:")
        for out in outputs2:
            if out["type"] == "stream":
                print(f"  Stream ({out['name']}): {out['text'].strip()}")
            elif out["type"] == "error":
                print(f"  Error: {out['ename']}: {out['evalue']}\n{out['traceback']}")

        print("\nAll executed cells:")
        for i, cell_info in enumerate(runtime.get_executed_cells()):
            print(f"Cell {i+1} Code:\n{cell_info['code']}")
            print(f"Cell {i+1} Outputs: {cell_info['outputs']}")
            print("---")

    except Exception as e:
        print(f"An error occurred during the demo: {e}")
    finally:
        # The atexit handler should take care of shutdown, but explicit call can be made if needed
        # if 'runtime' in locals() and runtime:
        #     runtime.shutdown_kernel()
        print("Runtime demo finished.")
