/**
 * CEREBRO — Master Application Coordinator
 */

const App = {
  currentAnalysis: null,
  activeTab: 'chat',

  async init() {
    console.log("⚡ CEREBRO Tone Intelligence Initializing...");

    // Initialize File Upload Dropzone
    Upload.init();

    // Setup Navigation Tabs
    this.setupNavigation();

    // Setup Global Action Buttons
    this.setupActions();

    // Setup Settings Form
    this.setupSettings();

    // Check backend health
    this.checkBackendHealth();

    // Auto-load sample chat on initial launch so the user sees the complete UI matching reference
    await this.autoLoadDefaultChat();
  },

  setupNavigation() {
    const navItems = Utils.$$('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        if (tab) {
          this.switchTab(tab);
        }
      });
    });
  },

  switchTab(tabName) {
    this.activeTab = tabName;

    // Update active class on nav
    Utils.$$('.nav-item').forEach(item => {
      if (item.getAttribute('data-tab') === tabName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Toggle active view sections
    Utils.$$('.view-section').forEach(section => {
      section.classList.remove('active');
    });

    const targetSection = document.getElementById(`view-${tabName}`);
    if (targetSection) {
      targetSection.classList.add('active');
    }

    // Refresh charts if entering arc or chat tab
    if (tabName === 'arc' && this.currentAnalysis) {
      setTimeout(() => {
        Charts.renderEmotionArc(this.currentAnalysis.timeline_arc);
      }, 50);
    } else if (tabName === 'chat' && this.currentAnalysis) {
      setTimeout(() => {
        Charts.renderEmotionDistribution(this.currentAnalysis.emotion_distribution, this.currentAnalysis.total_messages);
      }, 50);
    }
  },

  setupActions() {
    // Topbar Analyze Button
    const btnAnalyze = document.getElementById('btn-analyze-top');
    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => {
        this.runAnalysis();
      });
    }

    // Upload Preview "Analyze Now" Button
    const btnAnalyzePreview = document.getElementById('btn-analyze-preview');
    if (btnAnalyzePreview) {
      btnAnalyzePreview.addEventListener('click', () => {
        this.runAnalysis();
      });
    }

    // Participant Filter Dropdown
    const filterSelect = document.getElementById('participant-filter');
    if (filterSelect) {
      filterSelect.addEventListener('change', (e) => {
        if (this.currentAnalysis) {
          Conversation.renderMessages(this.currentAnalysis.messages, e.target.value);
        }
      });
    }

    // Replay Button
    const btnReplay = document.getElementById('btn-replay');
    if (btnReplay) {
      btnReplay.addEventListener('click', () => {
        if (!this.currentAnalysis) return;
        Conversation.startReplay(this.currentAnalysis.messages, (revealedMessages, latestMsg) => {
          // Dynamically update intensity during replay
          const intensityPct = latestMsg.emotional_intensity;
          document.getElementById('header-intensity-pill').innerText = `${intensityPct}% Intensity`;
        });
      });
    }

    // View All Highlights Link
    const linkViewAll = document.getElementById('link-view-all-highlights');
    if (linkViewAll) {
      linkViewAll.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchTab('insights');
      });
    }
  },

  async runAnalysis() {
    Utils.setLoading(true, 'Analyzing Conversation...', 'Computing multi-turn emotional state, detecting sarcasm and drift triggers');

    try {
      const payload = {};
      if (Upload.parsedData && Upload.parsedData.conversation_id) {
        payload.conversation_id = Upload.parsedData.conversation_id;
      }

      // Read custom sensitivity threshold if configured
      const thresholdInput = document.getElementById('setting-drift-threshold');
      if (thresholdInput) {
        payload.drift_threshold = parseFloat(thresholdInput.value);
      }

      const result = await Api.analyze(payload);
      this.currentAnalysis = result;

      // Update UI components
      this.renderAll(result);

      Utils.setLoading(false);
      Utils.showToast('Conversation successfully analyzed!', 'success');

      // Switch to Chat Dashboard view
      this.switchTab('chat');
    } catch (err) {
      Utils.setLoading(false);
      Utils.showToast(err.message, 'error');
    }
  },

  renderAll(data) {
    // 1. Conversation Header & Messages
    Conversation.renderHeader(data.filename, data.total_messages);
    Conversation.renderMessages(data.messages);

    // 2. Emotion Distribution Donut & Legend
    Charts.renderEmotionDistribution(data.emotion_distribution, data.total_messages);
    Dashboard.renderDistributionLegend(data.emotion_distribution);

    // 3. Highlights & Insights
    Dashboard.renderHighlights(data.highlights);
    Dashboard.renderInsights(data.insights);

    // 4. Emotion Arc Line Chart
    Charts.renderEmotionArc(data.timeline_arc);

    // 5. Key Moments ("Why did the tone change?")
    Dashboard.renderKeyMoments(data.key_moments);

    // 6. Participant Analysis Breakdown
    Dashboard.renderParticipants(data.participants_analysis);

    // 7. Topbar metrics
    const intensityBadge = document.getElementById('header-intensity-pill');
    if (intensityBadge) {
      intensityBadge.innerText = `${data.emotional_intensity}% Intensity`;
    }
    const escalationBadge = document.getElementById('header-escalation-pill');
    if (escalationBadge) {
      escalationBadge.innerText = `${data.escalation_level} Escalation`;
    }
  },

  async autoLoadDefaultChat() {
    try {
      const sample = await Api.loadSample();
      Upload.parsedData = sample;
      await this.runAnalysis();
    } catch (e) {
      console.warn("Backend not yet running or offline:", e.message);
    }
  },

  setupSettings() {
    const btnSave = document.getElementById('btn-save-settings');
    const apiInput = document.getElementById('setting-api-url');
    const geminiInput = document.getElementById('setting-gemini-key');
    const thresholdInput = document.getElementById('setting-drift-threshold');
    const thresholdVal = document.getElementById('drift-threshold-val');

    if (apiInput) {
      apiInput.value = Api.getBaseUrl();
    }

    if (thresholdInput && thresholdVal) {
      thresholdInput.addEventListener('input', (e) => {
        thresholdVal.innerText = e.target.value;
      });
    }

    if (btnSave) {
      btnSave.addEventListener('click', async () => {
        if (apiInput) {
          Api.setBaseUrl(apiInput.value.trim());
        }

        const settingsPayload = {};
        if (geminiInput && geminiInput.value.trim()) {
          settingsPayload.gemini_api_key = geminiInput.value.trim();
        }
        if (thresholdInput) {
          settingsPayload.drift_threshold = parseFloat(thresholdInput.value);
        }

        try {
          await Api.saveSettings(settingsPayload);
          Utils.showToast('Settings saved successfully', 'success');
          this.checkBackendHealth();
        } catch (e) {
          Utils.showToast('Saved locally, but server update failed', 'warning');
        }
      });
    }
  },

  async checkBackendHealth() {
    const health = await Api.checkHealth();
    const statusDot = document.getElementById('server-status-dot');
    const statusText = document.getElementById('server-status-text');

    if (health.status === 'healthy') {
      if (statusDot) statusDot.style.backgroundColor = '#10b981';
      if (statusText) statusText.innerText = health.gemini_configured ? 'Online • Gemini Active' : 'Online • Algorithmic NLP';
    } else {
      if (statusDot) statusDot.style.backgroundColor = '#ef4444';
      if (statusText) statusText.innerText = 'Backend Offline';
    }
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
