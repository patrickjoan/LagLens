BINDINGS = [
    ("q", "quit", "Quit"),
    ("s", "save_statistics", "Save Stats"),
    ("r", "refresh", "Refresh"),
]

CSS = """
    Screen {
        background: #202020;
        layout: horizontal;
    }
    
    .right-panel {
        background: #003366;
        width: 1fr;
        layout: vertical;
    }
    
    .right-bottom-panel {
        background: #252525;
        border: solid #404040;
        width: 1fr;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        margin: 1 0;
        min-height: 15;
    }
    
    #ping-results {
        height: auto;
        width: 1fr;
        padding: 1 2;
        background: #252525;
        border: solid #404040;
        overflow-y: auto;
    }
    
    #statistics {
        height: 1fr;
        width: 1fr;
        padding: 1 2;
        background: #252525;
        border: solid #404040;
        overflow-y: auto;
        min-height: 15;
    }
    
    #ascii-map {
        height: 1fr;
        width: 3fr;
        padding: 1 2;
        background: #252525;
        border: solid #404040;
        overflow-y: auto;
    }
    
    Header {
        background: #303030;
        color: white;
    }
    
    Footer {
        background: #303030;
        color: white;
    }
"""
