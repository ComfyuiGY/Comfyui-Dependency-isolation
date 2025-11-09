import { app } from "../../scripts/app.js";

// ComfyUI Dependency Isolation Web Extension
const EXTENSION_NAME = "ComfyDependencyIsolation";

function createDependencyManagerUI() {
    // Create a floating panel for dependency management
    const panel = document.createElement('div');
    panel.id = 'dependency-manager-panel';
    panel.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        z-index: 1000;
        max-width: 300px;
        backdrop-filter: blur(10px);
        border: 1px solid #555;
    `;

    panel.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong>🔒 Dependency Manager</strong>
            <button id="refresh-deps" style="background: #4CAF50; border: none; color: white; padding: 2px 8px; border-radius: 3px; cursor: pointer;">Refresh</button>
        </div>
        <div id="deps-status">Loading...</div>
    `;

    document.body.appendChild(panel);

    // Load dependency status
    function loadDependencyStatus() {
        fetch('/comfy_dependency_isolation/status')
            .then(response => response.json())
            .then(data => {
                updateStatusDisplay(data);
            })
            .catch(error => {
                document.getElementById('deps-status').innerHTML = 'Error loading status';
                console.error('Dependency status error:', error);
            });
    }

    function updateStatusDisplay(data) {
        const statusDiv = document.getElementById('deps-status');
        
        if (data.plugins && data.plugins.length > 0) {
            let html = `<div style="max-height: 200px; overflow-y: auto;">`;
            
            data.plugins.forEach(plugin => {
                html += `
                    <div style="margin-bottom: 6px; padding: 4px; background: rgba(255,255,255,0.1); border-radius: 3px;">
                        <div style="font-weight: bold;">${plugin.name}</div>
                        <div style="font-size: 10px; color: #ccc;">
                            Dependencies: ${plugin.dependency_count || 0}
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
            statusDiv.innerHTML = html;
        } else {
            statusDiv.innerHTML = 'No managed plugins found';
        }
    }

    // Refresh button event
    document.getElementById('refresh-deps').addEventListener('click', loadDependencyStatus);

    // Initial load
    loadDependencyStatus();

    // Auto-refresh every 30 seconds
    setInterval(loadDependencyStatus, 30000);
}

// Wait for ComfyUI to load
app.registerExtension({
    name: EXTENSION_NAME,
    async setup() {
        console.log('🔒 ComfyUI Dependency Isolation Web UI loaded');
        
        // Wait a bit for the page to fully load
        setTimeout(createDependencyManagerUI, 1000);
    },
});