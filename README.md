# NetSim: Network Simulator for Routing Protocols

NetSim is a Python-based network simulator designed to implement and test routing protocols such as Distance Vector (DV) and Link State (LS). It provides both a command-line interface for automated testing and a GUI for interactive visualization.

## Project Structure
```
routing/
|-- dv.py                # Distance Vector routing implementation
|-- ls.py                # Link State routing implementation
|-- main.py              # Entry point for running the simulator
|-- netsim/              # Core simulation engine
|   |-- __init__.py
|   |-- gui.py           # GUI implementation using wxPython
|   |-- router.py        # Base Router class
|   |-- simulation.py    # Core simulation logic
|-- requirements.txt     # Python dependencies
|-- tests/               # Test suite for DV and LS protocols
|   `-- tests.py
```

## Usage and Testing
### Running the Simulator
- **Debugging Mode (GUI):**
  - For Distance Vector (DV):
    ```bash
    python3 main.py -g -a dv
    ```
  - For Link State (LS):
    ```bash
    python3 main.py -g -a ls
    ```

- **Test Mode (non-GUI):**
  - For Distance Vector (DV):
    ```bash
    python3 main.py -a dv
    ```
  - For Link State (LS):
    ```bash
    python3 main.py -a ls
    ```

### Additional Options
- `-n N`: Set the number of nodes (default: 12).
- `-t T`: Set the simulation time (default: 2000).
- `-r`: Use a randomly generated topology.

For a full list of options, run:
```bash
python3 main.py -h
```

## GUI Visualization
The GUI allows you to:
- Visualize network nodes, links, and packet transmissions.
- Simulate link failures and observe routing updates.
- Click on nodes or links to view detailed information.

## Development
### Implementing Routing Protocols
- **Distance Vector (DV):** Complete the `integrate()` method in `dv.py`.

