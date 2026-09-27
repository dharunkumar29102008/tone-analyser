/**
 * CEREBRO — File Upload and File Validation Service
 */

const Upload = {
  selectedFile: null,
  parsedData: null,

  init() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const btnBrowse = document.getElementById('btn-browse-file');
    const btnSample = document.getElementById('btn-load-sample');
    const btnUploadHeader = document.getElementById('btn-upload-header');
    const btnChangeChat = document.getElementById('btn-change-chat');

    if (!dropzone || !fileInput) return;

    // Click to browse
    dropzone.addEventListener('click', (e) => {
      if (e.target !== btnSample) {
        fileInput.click();
      }
    });

    if (btnBrowse) {
      btnBrowse.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
      });
    }

    if (btnUploadHeader) {
      btnUploadHeader.addEventListener('click', () => {
        App.switchTab('upload');
      });
    }

    if (btnChangeChat) {
      btnChangeChat.addEventListener('click', () => {
        App.switchTab('upload');
      });
    }

    // Drag and drop events
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        this.handleFile(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        this.handleFile(e.target.files[0]);
      }
    });

    // Sample Chat 1-Click Load
    if (btnSample) {
      btnSample.addEventListener('click', async (e) => {
        e.stopPropagation();
        await this.loadSampleChat();
      });
    }
  },

  async handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.txt')) {
      Utils.showToast('Please select a valid WhatsApp exported .txt file', 'error');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      Utils.showToast('File size exceeds 5MB limit', 'error');
      return;
    }

    this.selectedFile = file;
    Utils.setLoading(true, 'Reading WhatsApp Chat File...', 'Validating timestamp formats and participant headers');

    try {
      const res = await Api.uploadFile(file);
      this.parsedData = res;
      Utils.setLoading(false);
      Utils.showToast(`Parsed ${res.total_messages} messages across ${res.participants.length} participants`, 'success');
      this.showFilePreview(res);
    } catch (err) {
      Utils.setLoading(false);
      Utils.showToast(err.message, 'error');
    }
  },

  async loadSampleChat() {
    Utils.setLoading(true, 'Loading Synthetic Sample Chat...', 'Loading friends_chat.txt dataset');
    try {
      const res = await Api.loadSample();
      this.parsedData = res;
      this.selectedFile = { name: 'friends_chat.txt' };
      Utils.setLoading(false);
      Utils.showToast('Loaded sample chat (friends_chat.txt)', 'success');
      this.showFilePreview(res);
    } catch (err) {
      Utils.setLoading(false);
      Utils.showToast(err.message, 'error');
    }
  },

  showFilePreview(data) {
    const previewContainer = document.getElementById('upload-preview-card');
    const previewName = document.getElementById('preview-filename');
    const previewMeta = document.getElementById('preview-file-meta');
    const participantsList = document.getElementById('preview-participants');

    if (previewContainer && previewName) {
      previewName.innerText = data.filename;
      previewMeta.innerText = `${data.total_messages} messages parsed`;
      if (participantsList) {
        participantsList.innerHTML = data.participants
          .map(p => `<span class="tone-badge badge-calm">${p}</span>`)
          .join(' ');
      }
      previewContainer.style.display = 'block';
    }
  }
};
