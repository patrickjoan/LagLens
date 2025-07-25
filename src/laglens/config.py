BINDINGS = [
    ("q", "quit", "Quit App"),
]

CSS = """
    Screen {
        background: #202020; /* Dark background */
        layout: horizontal;
    }

    .left-panel {
        background: #003366;
        width: 1fr;
    }
    .center-panel {
        background: #005599;
        width: 2fr;
    }
    .right-panel {
        background: #003366;
        width: 1fr;
    }
    #ping-results {
        height: 1fr; /* Take up available vertical space */
        width: 1fr; /* Take up available horizontal space */
        padding: 1 2; /* Vertical horizontal padding */
        background: #252525;
        border: solid #404040;
        overflow-y: auto; /* Enable scrolling if content overflows */
    }
    #ascii-map {
        height: 1fr; /* Take up available vertical space */
        width: 1fr; /* Take up available horizontal space */
        padding: 1 2; /* Vertical horizontal padding */
        background: #252525;
        border: solid #404040;
        overflow-y: auto; /* Enable scrolling if content overflows */
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
