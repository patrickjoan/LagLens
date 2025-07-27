# 🌍 LagLens - Network Latency Monitor

A terminal-based network latency monitoring tool that provides real-time visualization of server response times with ASCII world maps, sparkline graphs, and comprehensive statistics tracking. Made as part of [Boot.dev](https://www.boot.dev/ "Learn Backend Development") 2025 July hackathon.

Also i just wanted to make an ASCII map in the terminal.

## Screenshot

![LagLens in Action](assets/screenshot.png)

## Features

- **ASCII World Map** - Interactive world map showing server locations and status
- **Real-time Sparklines** - Visual latency trends with color-coded performance indicators
- **Live Statistics** - Min/Max/Average latency, jitter, and packet loss tracking
- **Dynamic Server Management** - Add custom servers at runtime through built-in forms
- **Historical Data** - Persistent latency history with statistics export
- **Rich Terminal UI** - Modern TUI with scrollable panels and keyboard shortcuts
- **Concurrent Monitoring** - Asynchronous pinging for optimal performance


## Requirements

- **Python**: 3.13+
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended)
- **Platform**: macOS, Linux, Windows (with WSL recommended)
- **Privileges**: Root/Administrator access for ICMP ping functionality

## Installation & Setup

### 1. Install uv (if not already installed)

Refer to the official [documentation](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Clone the Repository

```bash
git clone https://github.com/patrickjoan/LagLens.git
cd LagLens
```

### 3. Install Dependencies

```bash
# Install project dependencies
uv install

# Install development dependencies (optional)
uv install --group dev
```

### 4. Run LagLens

#### Standard Run:
```bash
uv run src/laglens/main.py
```

#### Alternative Direct Execution:
```bash
uv run python src/laglens/main.py
```

##  Usage

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit the application |
| `s` | Save Stats | Export statistics to JSON |
| `n` | Focus Form | Jump to add server form |
| `c` | Clear Form | Reset add server form |
| `Tab` | Navigate | Move between form fields |

### Adding Custom Servers

1. **Navigate to Form**: Use `n` or scroll to the bottom center panel
2. **Fill Required Fields**:
   - **Name**: Unique server identifier (e.g., `my-server-1`)
   - **IP Address**: Valid IPv4 address (e.g., `8.8.8.8`)
   - **Latitude**: Geographic coordinate (-90 to 90)
   - **Longitude**: Geographic coordinate (-180 to 180)
   - **City**: Optional location description
3. **Submit**: Click "Add Server" or press Enter
4. **Verify**: New server appears in monitoring panels immediately

### Example Test Servers

```
Google DNS:
Name: google-dns
IP: 8.8.8.8
Lat: 37.4056
Lon: -122.0775
City: Mountain View, CA

Cloudflare DNS:
Name: cloudflare-dns  
IP: 1.1.1.1
Lat: 37.7621
Lon: -122.3971
City: San Francisco, CA
```

## Configuration

### Server Definitions

Default AWS servers are defined in `src/laglens/config/servers.py`. Runtime servers are managed dynamically and persist for the session duration.

### UI Customization

Modify `src/laglens/config/laglens.tcss` to customize:
- Color schemes and themes
- Panel layouts and dimensions  
- Scrollbar styling
- Form input appearance
- Typography and spacing

### Application Settings

Key settings in `src/laglens/config/config.py`:
- Ping intervals and timeouts
- Latency thresholds for color coding
- Sparkline dimensions and history size
- Export formats and file locations

## Statistics Export

LagLens automatically tracks:
- **Response Times**: Min, Max, Average latency per server
- **Jitter**: Latency variance and stability metrics
- **Packet Loss**: Failed ping percentage
- **Historical Data**: Time-series latency measurements

Export data using `s` - creates timestamped JSON files with statistics.

## 🛠️ Development

### Adding New Features

1. **Follow the modular architecture** - separate concerns into appropriate modules
2. **Use the configuration system** - add settings to `config/config.py`
3. **Implement proper error handling** - graceful degradation for network issues
4. **Add keyboard shortcuts** - update `BINDINGS` in configuration
5. **Test with various servers** - validate against different network conditions

## 🐛 Troubleshooting

### Permission Issues
```bash
# macOS/Linux - run with sudo for ICMP access
sudo uv run src/laglens/main.py
```

### Dependencies Not Found
```bash
# Reinstall dependencies
uv sync --reinstall
```

### Import Errors
```bash
# Ensure you're in the project root directory
cd /path/to/LagLens
uv run src/laglens/main.py
```

### Performance Issues
- Reduce ping frequency in `config/config.py`
- Limit number of concurrent servers
- Check network connectivity and firewall settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
