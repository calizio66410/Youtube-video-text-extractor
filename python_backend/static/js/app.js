class ExtractorApp {
    constructor() {
        this.form = document.getElementById('extract-form');
        this.btnSubmit = document.getElementById('btn-submit');
        this.progressArea = document.getElementById('progress-area');
        this.resultsArea = document.getElementById('results-area');
        this.terminalLog = document.getElementById('terminal-log');
        this.progressBar = document.querySelector('.progress-bar-fill');
        this.statusText = document.getElementById('status-text');
        
        this.ws = null;
        this.currentJobId = null;
        this.resultData = null;

        this.initEventListeners();
    }

    initEventListeners() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });

        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                tab.classList.add('active');
                document.getElementById(tab.dataset.target).classList.add('active');
            });
        });

        const slider = document.getElementById('interval');
        const display = document.getElementById('interval-val');
        slider.addEventListener('input', () => { display.textContent = slider.value; });

        document.getElementById('btn-copy').addEventListener('click', () => this.copyToClipboard());
        document.getElementById('btn-dl-txt').addEventListener('click', () => this.downloadTxt());
        document.getElementById('btn-dl-srt').addEventListener('click', () => this.downloadSrt());
    }

    log(message) {
        const time = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.textContent = `[${time}] ${message}`;
        this.terminalLog.appendChild(line);
        this.terminalLog.scrollTop = this.terminalLog.scrollHeight;
    }

    async submitForm() {
        const url = document.getElementById('yt-url').value;
        const lang = document.getElementById('lang').value;
        const interval = parseFloat(document.getElementById('interval').value);
        const fastMode = document.getElementById('fast-mode').checked;

        if(!url) return;

        this.btnSubmit.disabled = true;
        this.progressArea.style.display = 'block';
        this.resultsArea.style.display = 'none';
        this.terminalLog.innerHTML = '';
        this.progressBar.style.width = '0%';
        this.log("Starting extraction pipeline...");

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, lang, interval, fast_mode: fastMode })
            });

            const data = await response.json();
            if(data.job_id) {
                this.currentJobId = data.job_id;
                this.connectWebSocket(data.job_id);
            } else {
                this.log("Error: " + JSON.stringify(data));
                this.btnSubmit.disabled = false;
            }
        } catch (error) {
            this.log("Network error: " + error.message);
            this.btnSubmit.disabled = false;
        }
    }

    connectWebSocket(jobId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/${jobId}`);

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateProgress(data);
        };
    }

    updateProgress(data) {
        if(data.message) {
            this.log(data.message);
            this.statusText.textContent = data.message;
        }
        if(data.progress !== undefined) {
            this.progressBar.style.width = `${data.progress}%`;
        }

        if(data.status === 'completed' && data.result) {
            this.ws.close();
            this.resultData = data.result;
            this.displayResults(data.result);
            this.btnSubmit.disabled = false;
            this.saveHistory(data.result);
        } else if (data.status === 'failed') {
            this.ws.close();
            this.btnSubmit.disabled = false;
        }
    }

    displayResults(result) {
        this.resultsArea.style.display = 'block';
        document.getElementById('result-textarea').value = result.data.text_with_timestamps;
        
        document.getElementById('stat-words').textContent = result.data.stats.total_words;
        document.getElementById('stat-blocks').textContent = result.data.stats.blocks;
        document.getElementById('stat-duration').textContent = result.data.stats.duration_covered_sec + ' s';
    }

    copyToClipboard() {
        const text = document.getElementById('result-textarea').value;
        navigator.clipboard.writeText(text);
    }

    downloadFile(content, filename, type) {
        const blob = new Blob([content], { type });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
    }

    downloadTxt() {
        if(this.resultData) this.downloadFile(this.resultData.data.text_with_timestamps, 'extraction.txt', 'text/plain');
    }

    downloadSrt() {
        if(this.resultData) this.downloadFile(this.resultData.data.srt, 'extraction.srt', 'text/plain');
    }

    saveHistory(result) {
        const history = JSON.parse(localStorage.getItem('extractor_history') || '[]');
        history.unshift({ title: result.info.title, date: new Date().toISOString() });
        localStorage.setItem('extractor_history', JSON.stringify(history.slice(0, 10)));
    }
}
document.addEventListener('DOMContentLoaded', () => window.app = new ExtractorApp());
