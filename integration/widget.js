/**
 * ShadeMate AI Widget — v1.0.0
 * Premium, Zero-Knowledge Skin Tone Matching for Shopify & WooCommerce.
 * 
 * INSTRUCTIONS:
 * 1. Host this file on your server or CDN.
 * 2. Add this tag to your store's <head>:
 *    <script src="widget.js" data-key="YOUR_API_KEY" data-api="https://your-api.com"></script>
 */

(function() {
    'use strict';

    // --- Configuration ---
    const scriptTag = document.currentScript;
    const API_KEY = scriptTag.getAttribute('data-key') || 'test-key-001';
    const API_BASE = scriptTag.getAttribute('data-api') || 'http://localhost:8000';
    
    // --- State ---
    let stream = null;

    // --- UI Elements (Injected) ---
    const styles = `
        :root {
            --sm-primary: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            --sm-glass: rgba(255, 255, 255, 0.7);
            --sm-dark: #1e293b;
        }

        #sm-widget-btn {
            background: var(--sm-primary);
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
            transition: all 0.3s ease;
            font-family: 'Inter', system-ui, sans-serif;
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 20px 0;
        }

        #sm-widget-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6);
        }

        #sm-modal-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 99999;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        #sm-modal {
            background: var(--sm-glass);
            width: 90%;
            max-width: 500px;
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            text-align: center;
            position: relative;
            font-family: 'Inter', system-ui, sans-serif;
        }

        #sm-video {
            width: 100%;
            border-radius: 16px;
            background: #000;
            transform: scaleX(-1);
            margin-bottom: 20px;
        }

        .sm-capture-btn {
            background: var(--sm-primary);
            width: 70px; height: 70px;
            border-radius: 50%;
            border: 4px solid white;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }

        .sm-capture-btn:active { transform: scale(0.9); }

        #sm-results {
            display: none;
            animation: slideUp 0.5s ease;
        }

        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .sm-match-card {
            background: white;
            padding: 15px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 15px;
            text-align: left;
            border: 1px solid #f1f5f9;
        }

        .sm-color-swatch {
            width: 50px; height: 50px;
            border-radius: 12px;
            flex-shrink: 0;
        }

        .sm-loader {
            display: none;
            width: 40px; height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #a855f7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    `;

    // --- Core Logic ---

    function init() {
        injectStyles();
        injectButton();
        createModal();
    }

    function injectStyles() {
        const styleTag = document.createElement('style');
        styleTag.innerHTML = styles;
        document.head.appendChild(styleTag);
    }

    function injectButton() {
        // Try to find "Add to Cart" button to place ShadeMate near it
        const selectors = ['.product-form__buttons', '.single_add_to_cart_button', '.add-to-cart', '[name="add"]'];
        let target = null;
        for(let s of selectors) {
            target = document.querySelector(s);
            if(target) break;
        }

        const btn = document.createElement('button');
        btn.id = 'sm-widget-btn';
        btn.innerHTML = `
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            Find Your Shade
        `;
        btn.onclick = openCamera;

        if(target) {
            target.parentNode.insertBefore(btn, target);
        } else {
            // Fallback: Fixed bottom right
            btn.style.position = 'fixed';
            btn.style.bottom = '20px';
            btn.style.right = '20px';
            document.body.appendChild(btn);
        }
    }

    function createModal() {
        const overlay = document.createElement('div');
        overlay.id = 'sm-modal-overlay';
        overlay.innerHTML = `
            <div id="sm-modal">
                <button style="position:absolute; top:15px; right:15px; background:none; border:none; font-size:20px; cursor:pointer;" onclick="window.smClose()">✕</button>
                <h2 style="margin-bottom:10px; color:var(--sm-dark)">Discover Your Shade</h2>
                <p style="margin-bottom:20px; color:#64748b; font-size:14px;">Center your face in the frame for the best result.</p>
                
                <div id="sm-camera-view">
                    <video id="sm-video" autoplay playsinline></video>
                    <button class="sm-capture-btn" onclick="window.smCapture()"></button>
                </div>

                <div id="sm-loader" class="sm-loader"></div>

                <div id="sm-results">
                    <h3 style="color:var(--sm-dark)">We found your match!</h3>
                    <div id="sm-match-list"></div>
                    <button id="sm-widget-btn" style="width:100%; margin-top:20px;" onclick="window.smClose()">Apply Recommendation</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        window.smClose = closeModal;
        window.smCapture = captureSelfie;
    }

    async function openCamera() {
        const overlay = document.getElementById('sm-modal-overlay');
        overlay.style.display = 'flex';
        setTimeout(() => overlay.style.opacity = '1', 10);

        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
            document.getElementById('sm-video').srcObject = stream;
        } catch (err) {
            alert('Camera access denied. Please upload a photo instead.');
            closeModal();
        }
    }

    function closeModal() {
        if(stream) stream.getTracks().forEach(t => t.stop());
        const overlay = document.getElementById('sm-modal-overlay');
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
            resetUI();
        }, 300);
    }

    function resetUI() {
        document.getElementById('sm-camera-view').style.display = 'block';
        document.getElementById('sm-results').style.display = 'none';
        document.getElementById('sm-loader').style.display = 'none';
        
        // Remove any old error messages
        const oldErr = document.getElementById('sm-error-msg');
        if(oldErr) oldErr.remove();
    }

    function validateImage(canvas) {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        let brightness = 0;
        for (let i = 0; i < data.length; i += 4) {
            brightness += (data[i] + data[i+1] + data[i+2]) / 3;
        }
        const avgBrightness = brightness / (data.length / 4);

        // SRS Standards
        if (canvas.width < 200 || canvas.height < 200) return "Image resolution too low.";
        if (avgBrightness < 40) return "Photo is too dark. Please find better lighting.";
        if (avgBrightness > 230) return "Photo is too bright. Please avoid direct glare.";
        
        return null; // Valid
    }

    async function captureSelfie() {
        const video = document.getElementById('sm-video');
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);

        // ── NEW: Client-Side Validation ──
        const error = validateImage(canvas);
        if (error) {
            const errDiv = document.createElement('div');
            errDiv.id = 'sm-error-msg';
            errDiv.style.color = '#ef4444';
            errDiv.style.marginTop = '10px';
            errDiv.style.fontSize = '14px';
            errDiv.innerHTML = `<strong>⚠️ ${error}</strong>`;
            
            const cameraView = document.getElementById('sm-camera-view');
            const oldErr = document.getElementById('sm-error-msg');
            if(oldErr) oldErr.remove();
            cameraView.appendChild(errDiv);
            return; // Stop here
        }

        // UI Transition
        document.getElementById('sm-camera-view').style.display = 'none';
        document.getElementById('sm-loader').style.display = 'block';

        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('image', blob, 'selfie.jpg');
            formData.append('client_id', 'demo-client');

            try {
                const res = await fetch(`${API_BASE}/analyze`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${API_KEY}` },
                    body: formData
                });
                
                const data = await res.json();
                if(data.status === 'success') {
                    showResults(data);
                } else {
                    alert('Analysis failed: ' + data.detail.message);
                    resetUI();
                }
            } catch (err) {
                alert('Network error connecting to ShadeMate AI.');
                resetUI();
            }
        }, 'image/jpeg', 0.8);
    }

    function deltaE(lab1, lab2) {
        return Math.sqrt(
            Math.pow(lab1.L - lab2.L, 2) +
            Math.pow(lab1.A - lab2.A, 2) +
            Math.pow(lab1.B - lab2.B, 2)
        );
    }

    function showResults(data) {
        document.getElementById('sm-loader').style.display = 'none';
        const resultsDiv = document.getElementById('sm-results');
        resultsDiv.style.display = 'block';

        const detectedLab = data.detected_skin.lab;
        
        // 1. Load Client Catalog (Mocked for demo, would be fetched from store in production)
        const catalog = [
            { id: "S1", name: "Ivory", hex: "#F6E5D3", lab: {L: 92.1, A: 1.2, B: 9.5} },
            { id: "S2", name: "Natural Beige", hex: "#E1BC9B", lab: {L: 78.4, A: 6.2, B: 18.5} },
            { id: "S3", name: "Honey", hex: "#D4A76A", lab: {L: 69.2, A: 5.4, B: 38.1} },
            { id: "S4", name: "Bronze", hex: "#A17249", lab: {L: 48.2, A: 12.1, B: 24.5} }
        ];

        // 2. Score everything
        let scoredProducts = catalog.map(p => {
            const diff = deltaE(detectedLab, p.lab);
            const score = Math.max(0, Math.min(100, 100 - diff));
            return { ...p, score: Math.round(score) };
        }).sort((a, b) => b.score - a.score);

        // 3. Cascading Threshold Logic
        let matches = scoredProducts.filter(p => p.score >= 75);
        let label = "Top Recommendations for You";

        if (matches.length === 0) {
            matches = scoredProducts.filter(p => p.score >= 55);
            label = "Suggested Shade Matches";
        }

        if (matches.length === 0) {
            matches = scoredProducts.slice(0, 2); // Show top 2 regardless
            label = "Closest Available Options";
        }

        const matchList = document.getElementById('sm-match-list');
        document.querySelector('#sm-results h3').innerText = label;
        
        matchList.innerHTML = matches.map(m => `
            <div class="sm-match-card">
                <div class="sm-color-swatch" style="background:${m.hex}"></div>
                <div style="flex:1">
                    <strong style="display:block; font-size:16px;">${m.name}</strong>
                    <span style="color:#64748b; font-size:13px;">${m.score}% Color Compatibility</span>
                </div>
                <button style="background:#f1f5f9; border:none; padding:8px 12px; border-radius:8px; font-size:12px; cursor:pointer;" onclick="location.href='/products/${m.id}'">View</button>
            </div>
        `).join('');
    }

    // --- Initialize ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
